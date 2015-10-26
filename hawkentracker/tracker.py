# -*- coding: utf-8 -*-
# Hawken Tracker - Player/Match Tracker

import logging
from datetime import datetime

from sqlalchemy.orm import contains_eager
from flask import current_app

from hawkentracker.interface import get_api, api_wrapper, get_redis, format_redis_key
from hawkentracker.database import db, Player, PlayerStats, Match, MatchPlayer, PollLog, UpdateJournal
from hawkentracker.database.util import windowed_query
from hawkentracker.mappings import ranking_fields, region_groupings, UpdateFlag, UpdateStatus, UpdateStage

logger = logging.getLogger(__name__)


def update_seen_players(players, poll_time):
    logger.info("[Players] Updating seen players")

    # Load callsigns
    logger.debug("[Players] Loading player callsigns")
    callsigns = api_wrapper(lambda: get_api().get_user_callsign(players, cache_skip=True))

    # Collect existing player data
    existing_players = db.session.query(Player.id, Player.callsign).filter(Player.id.in_(players)).all()
    new_players = list(set(players).difference((guid for guid, _ in existing_players)))

    # Update existing players
    logger.debug("[Players] Updating existing players")
    Player.query.filter(Player.id.in_(players)).update({Player.last_seen: poll_time}, synchronize_session=False)
    for guid, new_callsign in ((guid, callsigns[guid]) for guid, callsign in existing_players if guid in callsigns and callsign != callsigns[guid]):
        Player.query.filter(Player.id == guid).update({Player.callsign: new_callsign}, synchronize_session=False)

    if len(new_players) > 0:
        # Add new players
        logger.debug("[Players] Adding new players")
        for guid in new_players:
            player = Player(id=guid)
            player.callsign = callsigns.get(guid, None)
            player.update(poll_time)
            db.session.add(player)

    return len(existing_players), len(new_players)


def update_seen_matches(matches, poll_time):
    logger.info("[Matches] Updating seen matches")

    # Update existing matches
    logger.debug("[Matches] Updating existing matches")
    found = []
    for match in Match.query.filter(Match.id.in_(matches.keys())):
        found.append(match.id)
        match.update(matches[match.id], poll_time)
        db.session.add(match)

        # Update match players
        update_match_players(match, matches[match.id]["Users"], poll_time)

    # Add new matches
    logger.debug("[Matches] Adding new matches")
    for match_id in (match_id for match_id in matches.keys() if match_id not in found):
        match = Match(id=match_id)
        match.update(matches[match.id], poll_time)
        db.session.add(match)

        # Add match players
        add_match_players(match, matches[match.id]["Users"], poll_time)

    return len(found), len(matches) - len(found)


def update_match_players(match, players, poll_time):
    if len(players) > 0:
        # Update existing players
        found = []
        for matchplayer in MatchPlayer.query.filter(MatchPlayer.match_id == match.id, MatchPlayer.player_id.in_(players)):
            found.append(matchplayer.player_id)
            matchplayer.update(poll_time)
            db.session.add(matchplayer)

        # Add new players
        for player in (player for player in players if player not in found):
            matchplayer = MatchPlayer(match_id=match.id, player_id=player)
            matchplayer.update(poll_time)
            db.session.add(matchplayer)


def add_match_players(match, players, poll_time):
    # Add new players
    for player in players:
        matchplayer = MatchPlayer(match_id=match.id, player_id=player)
        matchplayer.update(poll_time)
        db.session.add(matchplayer)


def update_players(last, journal):
    logger.info("[Players] Updating players")

    if UpdateFlag.all_players in journal.flags:
        last = None

    # Iterate over the players
    for i, chunk in windowed_query(Player.query, Player.last_seen, current_app.config["TRACKER_BATCH_SIZE"],
                                   begin=last,
                                   end=journal.start,
                                   journal=journal,
                                   logger=logger,
                                   logger_prefix="[Players]"):
        # Update the stats
        logger.debug("[Players] Updating stats for chunk %d", i + 1)
        update_player_stats(chunk, journal.start)

        # Update the region
        logger.debug("[Players] Updating regions for chunk %d", i + 1)
        update_player_regions(chunk)

        if UpdateFlag.update_callsigns in journal.flags:
            # Update the callsigns
            logger.debug("[Players] Updating callsigns for chunk %d", i + 1)
            journal.callsigns_updated += update_player_callsigns(chunk)

        journal.players_updated += len(chunk)


def update_player_stats(players, update_time):
    ids = [player.id for player in players]

    # Load the stats
    # Using the cache here can fill up the redis backend with player data, so we skip it here.
    stats = {data["Guid"]: data for data in api_wrapper(lambda: get_api().get_user_stats(ids, cache_skip=True))}

    # Update players
    for player in players:
        if player.id in stats:
            player_stats = PlayerStats(player_id=player.id, snapshot_taken=update_time)
            player_stats.update(stats[player.id])
            db.session.add(player_stats)


def update_player_regions(players):
    # Iterate through the players
    for player in players:
        # Detect most common region
        regions_query = db.session.query(Match.server_region, db.func.count(Match.server_region)).\
                                   join(MatchPlayer).\
                                   filter(MatchPlayer.player_id == player.id).\
                                   group_by(Match.server_region)

        # Group regions
        regions = {}
        for region, count in regions_query.all():
            region = region_groupings.get(region, region)
            regions[region] = regions.get(region, 0) + count

        if len(regions) > 0:
            # Update the region
            player.common_region = max(regions.keys(), key=lambda k: regions[k])
            db.session.add(player)


def update_player_callsigns(players):
    # Load the callsigns
    callsigns = api_wrapper(lambda: get_api().get_user_callsign([player.id for player in players], cache_skip=True))

    # Iterate through the players
    count = 0
    for player in (player for player in players if player.id in callsigns and player.callsign != callsigns[player.id]):
        player.callsign = callsigns[player.id]
        db.session.add(player)
        count += 1

    return count


def update_matches(last, journal):
    logger.info("[Matches] Updating matches")

    if UpdateFlag.all_matches in journal.flags:
        last = None

    # Iterate over the matches
    for _, match in windowed_query(Match.query, Match.last_seen, current_app.config["TRACKER_BATCH_SIZE"],
                                   begin=last,
                                   end=journal.start,
                                   streaming=True,
                                   journal=journal,
                                   logger=logger,
                                   logger_prefix="[Matches]"):
        # Update the stats
        update_match_stats(match, journal.start)

        journal.matches_updated += 1


def update_match_stats(match, update_time):
    # Get the player stats for the match
    stats = db.session.query(PlayerStats.mmr, PlayerStats.pilot_level).\
                       join(MatchPlayer, PlayerStats.player_id == MatchPlayer.player_id).\
                       filter(MatchPlayer.match_id == match.id).all()

    if len(stats) > 0:
        # Unpack and update match stats
        mmrs, levels = zip(*stats)
        match.calculate_stats([mmr for mmr in mmrs if mmr is not None], levels, update_time)
        db.session.add(match)


def update_global_rankings(last, journal):
    logger.info("[Rankings] Updating global rankings")
    redis = get_redis()

    # Prep journal
    i = journal.stage_start(len(ranking_fields))
    db.session.commit()

    # Latest snapshot filter subquery
    ps1 = db.aliased(PlayerStats)
    latest_snapshot = db.session.query(db.func.max(ps1.snapshot_taken)).filter(ps1.player_id == PlayerStats.player_id).subquery()

    # Iterate over the rankings
    for field in ranking_fields[i:]:
        key = format_redis_key("rank", field)

        logger.debug("[Rankings] Updating global rankings for %s", field)

        # Delete old rankings
        redis.delete(key)

        # Get the target field and it's default
        target = getattr(PlayerStats, field)
        if target.default is None:
            default = target.default
        else:
            default = target.default.arg

        # Iterate over the players, building the current field's rankings
        query = db.session.query(PlayerStats.player_id, target).\
                           join(Player).\
                           filter(target != default).\
                           filter(Player.blacklisted.is_(False)).\
                           filter(PlayerStats.snapshot_taken == latest_snapshot).\
                           order_by(target.desc())

        # Setup for the loop
        index = 0
        position = 0
        last = False
        batch = {}
        for player, score in query.yield_per(current_app.config["TRACKER_BATCH_SIZE"]):
            # Update the index and position
            index += 1
            if last != score:
                position = index
            last = score

            # Set player's position
            batch[player] = position

            if index % current_app.config["TRACKER_BATCH_SIZE"] == 0:
                # Save the chunk of players
                redis.hmset(key, batch)
                batch = {}

        # Set the total number of ranked players
        batch["total"] = index
        redis.hmset(key, batch)

        i += 1
        journal.stage_checkpoint(i)
        db.session.commit()

    journal.global_rankings_updated = True
    db.session.commit()


def poll_servers():
    # Setup for the poll
    players_count = 0
    matches_count = 0
    success = True
    start = datetime.now()

    try:
        api = get_api()

        # Get the server list data (bypassing the cache to get a fresh snapshot)
        logger.info("[Poll] Loading server list")
        server_list = api_wrapper(lambda: api.get_server_list(cache_bypass=True))

        players = set()
        for server in server_list:
            for player in server["Users"]:
                players.add(player)
        players = list(players)
        players_count = len(players)

        # Ignore the matches with no players. This means matches will only be considered to exist while there is a
        # player in it. Considering that servers are subject to kills and restarts when idle, and we are tracking
        # players and not matches, we can save some time and space ignoring all the empty matches.
        matches = {server["MatchId"]: server for server in server_list if server["MatchId"] is not None and len(server["Users"]) > 0}
        matches_count = len(matches)

        if players_count > 0:
            with db.session.no_autoflush:
                # Update players
                update_seen_players(players, start)

        if matches_count > 0:
            with db.session.no_autoflush:
                # Update matches
                update_seen_matches(matches, start)

        # Commit the players and matches
        logger.debug("[Poll] Committing data")
        db.session.commit()
    except:
        logger.error("Exception encountered, rolling back...")
        success = False
        try:
            db.session.rollback()
        except:
            logger.critical("Failed to roll back session!")
            raise
        raise
    finally:
        # Record the update session
        PollLog.record(success, start, datetime.now(), players_count, matches_count)
        db.session.commit()

    return players_count, matches_count


def update_tracker(flags, resume=False):
    # Prepare journal
    start = datetime.now()
    journal = UpdateJournal.last()
    if journal is None or journal.status == UpdateStatus.complete:
        if resume:
            logger.warn("No previous update to resume! Starting new update.")

        journal = UpdateJournal(start=start, flags=flags, status=UpdateStatus.not_started, stage=UpdateStage.not_started)
    elif journal.status in (UpdateStatus.in_progress, UpdateStatus.not_started):
        logger.error("Previous in-progress update found! Refusing to start a new update.")
        return journal
    elif resume:
        logger.info("Resuming previous update.")
        if sorted(flags) != sorted(journal.flags):
            logger.warn("Provided flags do not match journal's flags! Using journal flags.")
    else:
        journal = UpdateJournal(start=start, flags=flags, status=UpdateStatus.not_started, stage=UpdateStage.not_started)

    journal.status = UpdateStatus.in_progress
    db.session.add(journal)
    db.session.commit()

    try:
        # Get the last completed update
        last = UpdateJournal.last_completed()

        with db.session.no_autoflush:
            if journal.stage == UpdateStage.not_started:
                # Start with players
                journal.stage_next(UpdateStage.players)

            if journal.stage == UpdateStage.players:
                # Update the player data
                update_players(last, journal)

                # Move onto matches
                journal.stage_next(UpdateStage.matches)
                db.session.commit()

            if journal.stage == UpdateStage.matches:
                # Update the match stats
                update_matches(last, journal)

                # Move onto global rankings
                journal.stage_next(UpdateStage.global_rankings)
                db.session.commit()

            if journal.stage == UpdateStage.global_rankings:
                # Update the global rankings
                update_global_rankings(last, journal)

                # Move onto completion
                journal.stage_next(UpdateStage.complete)
                db.session.commit()
    except:
        logger.error("Exception encountered, rolling back...", exc_info=True)
        try:
            db.session.rollback()
        except:
            logger.critical("Failed to roll back session!", exc_info=True)

        # Record failure
        journal.fail(start)
    else:
        # Record completion
        journal.complete(start)
    finally:
        # Commit the journal
        db.session.commit()

    return journal


def decode_rank(rank):
    if rank is None:
        return None
    return int(rank)


def get_global_rank(player, field):
    redis = get_redis()
    total = decode_rank(redis.hget(format_redis_key("rank", field), "total"))

    if isinstance(player, str):
        return decode_rank(redis.hget(format_redis_key("rank", field), player)), total

    if len(player) > 0:
        return {player: decode_rank(rank) for player, rank in zip(player, redis.hmget(format_redis_key("rank", field), player))}, total

    return {}, total


def get_ranked_players(field, count, preload=None):
    # Make sure we aren't doing a pointless request
    if count < 1:
        raise ValueError("You must request at least one player")

    if preload is None:
        preload = []

    # Get the target field
    target = getattr(PlayerStats, field)

    # Get the default value for the target attribute
    if target.default is None:
        default = target.default
    else:
        default = target.default.arg

    # Build the query
    query = Player.query.join(Player.stats).filter(target != default).filter(Player.blacklisted.is_(False))
    if preload:
        query = query.options(contains_eager(Player.stats))
    query = query.order_by(target.desc())
    if target != PlayerStats.mmr:
        # This is a secondary sort in case there is conflicts
        query = query.order_by(PlayerStats.mmr.desc())

    # Get the top list of players
    return query[:count]
