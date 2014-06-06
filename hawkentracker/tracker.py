# -*- coding: utf-8 -*-
# Hawken Tracker - Player/Match Tracker

import time
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import contains_eager, joinedload
from hawkentracker.interface import get_api, api_wrapper, get_redis, format_redis_key
from hawkentracker.model import db, Player, PlayerStats, Match, MatchPlayer, Group, GroupPlayer, PollLog, UpdateLog
from hawkentracker.mappings import Confirmation, ranking_fields


def update_seen_players(players, poll_time):
    # Update existing players
    found = []
    for player in Player.query.filter(Player.id.in_(players)):
        found.append(player.id)
        player.update(poll_time)
        db.session.add(player)

    # Add new players
    for guid in (guid for guid in players if guid not in found):
        player = Player(id=guid)
        player.update(poll_time)
        db.session.add(player)


def update_seen_matches(matches, poll_time):
    # Update existing matches
    found = []
    for match in Match.query.filter(Match.id.in_(matches.keys())):
        found.append(match.id)
        match.update(matches[match.id], poll_time)
        db.session.add(match)

        # Update match players
        if len(matches[match.id]["Users"]) > 0:
            update_match_players(match.id, matches[match.id]["Users"], poll_time)

    # Add new matches
    for matchid in (matchid for matchid in matches.keys() if matchid not in found):
        match = Match(id=matchid)
        match.update(matches[matchid], poll_time)
        db.session.add(match)

        # Add match players
        if len(matches[matchid]["Users"]) > 0:
            add_match_players(matchid, matches[matchid]["Users"], poll_time)


def add_match_players(match, players, poll_time):
    # Add new players
    for player in players:
        matchplayer = MatchPlayer(match_id=match, player_id=player)
        matchplayer.update(poll_time)
        db.session.add(matchplayer)


def update_match_players(match, players, poll_time):
    # Update existing players
    found = []
    for matchplayer in MatchPlayer.query.filter(MatchPlayer.match_id == match, MatchPlayer.player_id.in_(players)):
        found.append(matchplayer.player_id)
        matchplayer.update(poll_time)
        db.session.add(matchplayer)

    # Add new players
    for player in (player for player in players if player not in found):
        matchplayer = MatchPlayer(match_id=match, player_id=player)
        matchplayer.update(poll_time)
        db.session.add(matchplayer)


def update_players(last):
    api = get_api()

    # Get the list of players to update
    query = Player.query
    if last is not None:
        query = query.filter(Player.last_seen > last)
    players = query.all()
    ids = [player.id for player in players]

    if len(ids) > 0:
        # Load the player stats
        update_time = datetime.now()

        stats = {data["Guid"]: data for data in api_wrapper(lambda: api.get_user_stats(ids))}

        # Update existing players
        found = []
        for playerstats in PlayerStats.query.filter(PlayerStats.player_id.in_(ids)):
            found.append(playerstats.player_id)
            playerstats.update(stats[playerstats.player_id], update_time)
            db.session.add(playerstats)

        # Add new players
        for player in (player for player in ids if player not in found):
            playerstats = PlayerStats(player_id=player)
            playerstats.update(stats[player], update_time)
            db.session.add(playerstats)

        # Update detected regions
        for player in players:
            regions = db.session.query(Match.server_region, func.count(Match.server_region)).join(MatchPlayer).\
                filter(MatchPlayer.player_id == player.id).group_by(Match.server_region).all()

            try:
                player.common_region = max(regions, key=lambda x: x[1])[0]
            except ValueError:
                pass
            else:
                db.session.add(player)

    return len(ids)


def update_matches(last):
    # Get the list of matches to update
    query = Match.query.options(joinedload(Match.players))
    if last is not None:
        query = query.filter(Match.last_seen > last)
    matches = query.all()

    # Update the averages for each match
    i = 0
    for match in query:
        update_match_averages(match)
        i += 1

    return i


def update_match_averages(match):
    # Get the list of players for the match
    players = [player.player_id for player in match.players]

    # Get the player mmrs and levels
    mmrs = []
    levels = []
    for mmr, level in db.session.query(PlayerStats.mmr, PlayerStats.pilot_level).filter(PlayerStats.player_id.in_(players)):
        if mmr != 0.0:
            mmrs.append(mmr)
        levels.append(level)

    # Update stats
    if len(mmrs) > 0:
        match.average_mmr = sum(mmrs) / len(mmrs)
    if len(levels) > 0:
        match.average_level = sum(levels) / len(levels)
    db.session.add(match)


def update_global_rankings(players):
    redis = get_redis()

    # Drop all known players
    redis.delete(*(format_redis_key("rank", player) for player in players))

    # Iterate over each ranking and append it to the list one at a time
    for field in ranking_fields:
        # Get the target field
        target = getattr(PlayerStats, field)
        if target.default is None:
            default = target.default
        else:
            default = target.default.arg

        # Setup for the loop
        i = 0
        p = 0
        last = False
        pipe = redis.pipeline(transaction=False)
        # Iterate over the players and build the current field's ranking
        for id, value in db.session.query(PlayerStats.player_id, target).filter(target != default).order_by(target.desc()):
            # Update the index and position
            i += 1
            if last != value:
                p = i

            # Add the ranking for the field to the player's rank info
            if value is not None:
                pipe.hset(format_redis_key("rank", id), field, p)

            # Setup for the next iteration
            last = value

        # Flush the last ranking
        pipe.execute()


def update_group_rankings(players):
    redis = get_redis()

    for group in db.session.query(Group.id):
        # Drop all possible players - prevents dangling records from players who left the group
        redis.delete(*(format_redis_key("grouprank", group, player) for player in players))

        # Iterate over each ranking and append it to the list one at a time
        for field in ranking_fields:
            # Get the target field
            target = getattr(PlayerStats, field)
            if target.default is None:
                default = target.default
            else:
                default = target.default.arg

            # Setup for the loop
            i = 0
            p = 0
            last = False
            pipe = redis.pipeline(transaction=False)
            # Iterate over the players and build the current field's ranking
            for id, value in db.session.query(PlayerStats.player_id, target).\
                                        join(GroupPlayer, PlayerStats.player_id == GroupPlayer.player_id).\
                                        filter(target != default).\
                                        filter(GroupPlayer.group_id == group).\
                                        filter(GroupPlayer.confirmation == Confirmation.both).\
                                        order_by(target.desc()):
                # Update the index and position
                i += 1
                if last != value:
                    p = i

                # Add the ranking for the field to the player's rank info
                if value is None:
                    pipe.hset(format_redis_key("grouprank", group, id), field, p)

                # Setup for the next iteration
                last = value

            # Flush the last ranking
            pipe.execute()


def poll_servers():
    # Setup for the poll
    players_count = 0
    matches_count = 0
    success = True
    start = datetime.now()

    try:
        api = get_api()

        # Get the server list data
        server_list = api_wrapper(lambda: api.get_server_list())

        players = set()
        for server in server_list:
            for player in server["Users"]:
                players.add(player)
        players_count = len(players)
        # Ignore the matches with no players. Ignoring the empty matches means it will only appear when a match has
        # players and will disappear when the match no longer has any players in it. This is ok, considering that
        # servers are subject to kills and restarts when idle anyway, and in the end, we are tracking players here, not
        # empty matches.
        matches = {server["MatchId"]: server for server in server_list if server["MatchId"] is not None and len(server["Users"]) > 0}
        matches_count = len(matches)

        # Update data
        if players_count > 0:
            update_seen_players(players, start)
        if matches_count > 0:
            update_seen_matches(matches, start)
        db.session.commit()
    except:
        success = False
        db.session.rollback()
        raise
    finally:
        # Record the update session
        PollLog.record(success, start, datetime.now(), players_count, matches_count)
        db.session.commit()

    return players_count, matches_count


def update_all(force=False):
    success = True
    players = 0
    matches = 0
    rankings = False
    start = datetime.now()

    try:
        if force:
            # Force full update
            last = None
        else:
            # Get the last update
            last = UpdateLog.last()

        # Update the player data
        players = update_players(last)

        # Update the match stats
        matches = update_matches(last)

        # Commit the data before doing the rankings
        db.session.commit()
    except:
        success = False
        db.session.rollback()
        raise
    else:
        # Update the rankings
        ids = [item[0] for item in db.session.query(Player.id)]
        update_global_rankings(ids)
        update_group_rankings(ids)
        rankings = True
    finally:
        # Record the update session
        UpdateLog.record(success, start, datetime.now(), players, matches, rankings)
        db.session.commit()

    return players, matches, rankings


def decode_rank(rank):
    if rank is None:
        return None

    if isinstance(rank, dict):
        return {k.decode(): int(v.decode()) for k, v in rank.items()}

    return int(rank.decode())


def get_global_rank(player, field=None):
    redis = get_redis()

    if field is None:
        return decode_rank(redis.hgetall(format_redis_key("rank", player)))
    return decode_rank(redis.hget(format_redis_key("rank", player), field))


def get_group_rank(group, player, field=None):
    redis = get_redis()

    if field is None:
        return decode_rank(redis.hgetall(format_redis_key("grouprank", group, player)))
    return decode_rank(redis.hget(format_redis_key("grouprank", group, player), field))


def get_top_players(count, sort, preload=None):
    if preload is None:
        preload = []

    # Make sure we aren't doing a pointless request
    if count < 1:
        raise ValueError("You must request at least one player")

    # Get the target and default value
    target = getattr(PlayerStats, sort)
    if target.default is None:
        default = target.default
    else:
        default = target.default.arg

    # Build the query
    query = Player.query.join(Player.stats).filter(target != default)
    if preload:
        query = query.options(contains_eager(Player.stats).load_only("last_updated", sort, *preload))
    query = query.order_by(target.desc())
    if target != PlayerStats.mmr:
        # This is a secondary sort in case there is a bunch of conflicts
        query = query.order_by(PlayerStats.mmr.desc())

    # Get the top list of players
    return query[:count]
