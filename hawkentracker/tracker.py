# -*- coding: utf-8 -*-
# Hawken Tracker - Player/Match Tracker

import logging
import itertools
from datetime import datetime
from functools import wraps

from sqlalchemy.orm import contains_eager
from flask import current_app

from hawkentracker.interface import get_api, api_wrapper, get_redis, format_redis_key
from hawkentracker.database import db, Player, PlayerStats, Match, MatchPlayer, PollJournal, UpdateJournal
from hawkentracker.database.util import HandleUniqueViolation, windowed_query
from hawkentracker.mappings import PollFlag, PollStatus, PollStage, UpdateFlag, UpdateStatus, UpdateStage,\
    ranking_fields, region_groupings

logger = logging.getLogger(__name__)


class CallsignConflictResolver:
    def __init__(self, logger, callsigns):
        self.logger = logger
        self.callsigns = callsigns

    def __call__(self, f):
        @HandleUniqueViolation(db.session, self.resolver, "ix_players_callsign")
        @wraps(f)
        def wrap(*args, **kwargs):
            return f(*args, **kwargs)

        return wrap

    def resolver(self, e_orig):
        self.logger.warn("Callsign conflict encountered, resolving...")

        # Resolve callsigns
        conflicted_users = self.resolve_callsigns()

        # Unset callsigns for conflicting users to prevent inter-update conflicts
        # The other method to dealing with this would be active conflict resolution, but as these conflicts should be
        # small, just clearing them should be fast enough.
        Player.query.filter(Player.player_id.in_(list(conflicted_users.keys()))).update({Player.callsign: None}, synchronize_session=False)

        # Update callsigns for conflicting users
        for guid, new_callsign in conflicted_users:
            Player.query.filter(Player.player_id == guid).update({Player.callsign: new_callsign}, synchronize_session=False)

    def resolve_callsigns(self):
        resolved_conflicts = {}

        # Get the first set of conflicts
        db_result = db.session.query(Player.player_id, Player.callsign).filter(self.callsign_filter(self.callsigns)).all()

        # Assert we have at least some conflicts
        assert len(db_result) > 0, "Encountered callsign conflict but found no conflicts! Checked callsigns: %s" % self.callsigns.values()

        while len(db_result) > 0:
            # Get updated callsigns for conflicted users
            new_callsigns = api_wrapper(lambda: get_api().get_user_callsign([x for x, _ in db_result], cache_skip=True))

            for guid, old, new in ((guid, callsign, new_callsigns[guid]) for guid, callsign in db_result):
                # Assert the callsign actually changed before adding to resolved conflicts
                assert old != new, "Callsign conflict on %s resolved to same callsign: %s" % (guid, new)
                resolved_conflicts[guid] = new

            # Check new callsigns for conflicts
            db_result = db.session.query(Player.player_id, Player.callsign).filter(self.callsign_filter(new_callsigns)).all()

        return resolved_conflicts

    def callsign_filter(self, callsigns):
        return db.func.lower(Player.callsign).in_([callsign.lower() for callsign in callsigns.values()])


def load_server_list(journal):
    api = get_api()

    # Get the server list data (bypassing the cache to get a fresh snapshot)
    logger.info("[Servers] Loading server list")
    server_list = api_wrapper(lambda: api.get_server_list(cache_bypass=True))

    # Collect players
    players = list(set(itertools.chain.from_iterable((server["Users"] for server in server_list))))

    # Collect matches
    matches = {server["MatchId"]: server for server in server_list if server["MatchId"] is not None}

    if PollFlag.empty_matches not in journal.flags:
        # Ignore the matches with no players. This means matches will only be considered to exist while there is a
        # player in it. Considering that servers are subject to kills and restarts when idle, and we are tracking
        # players and not matches, we can save some time and space ignoring all the empty matches.
        matches = {match_id: server for match_id, server in matches.items() if len(server["Users"]) > 0}

    return players, matches


def update_seen_players(players, journal):
    logger.info("[Players] Updating seen players")

    # Collect existing players
    existing_players = [guid for guid, in db.session.query(Player.player_id).filter(Player.player_id.in_(players))]

    # Update existing players
    logger.debug("[Players] Updating existing players")
    Player.query.filter(Player.player_id.in_(existing_players)).update({Player.last_seen: journal.start}, synchronize_session=False)

    # Collect new players
    new_players = list(set(players).difference(existing_players))

    if len(new_players) > 0:
        # Load callsigns
        logger.debug("[Players] Loading player callsigns")
        callsigns = api_wrapper(lambda: get_api().get_user_callsign(new_players, cache_skip=True))

        @CallsignConflictResolver(logger, callsigns)
        def add_players(players, callsigns):
            # Add new players
            logger.debug("[Players] Adding new players")
            for guid in players:
                player = Player(player_id=guid)
                player.callsign = callsigns.get(guid, None)
                player.seen(journal.start)
                db.session.add(player)

        add_players(new_players, callsigns)

    journal.players_updated = len(existing_players)
    journal.players_added = len(new_players)


def update_seen_matches(matches, journal):
    logger.info("[Matches] Updating seen matches")

    # Update existing matches
    logger.debug("[Matches] Updating existing matches")
    existing_matches = []
    for match in Match.query.filter(Match.match_id.in_(matches.keys())):
        existing_matches.append(match.match_id)
        match.seen(journal.start)
        match.load_server_info(matches[match.match_id])
        db.session.add(match)

        players = matches[match.match_id]["Users"]

        # Update match players
        if len(players) > 0:
            # Update existing players
            existing_players = []
            for matchplayer in MatchPlayer.query.filter(MatchPlayer.match_id == match.match_id, MatchPlayer.player_id.in_(players)):
                existing_players.append(matchplayer.player_id)
                matchplayer.seen(journal.start)
                db.session.add(matchplayer)

            # Add new players
            for player in set(players).difference(existing_players):
                matchplayer = MatchPlayer(match_id=match.match_id, player_id=player)
                matchplayer.seen(journal.start)
                db.session.add(matchplayer)

    # Collect new matches
    new_matches = list(set(matches.keys()).difference(existing_matches))

    # Add new matches
    logger.debug("[Matches] Adding new matches")
    for match_id in new_matches:
        match = Match(match_id=match_id)
        match.seen(journal.start)
        match.load_server_info(matches[match.match_id])
        db.session.add(match)

        # Add match players
        for player in matches[match.match_id]["Users"]:
            matchplayer = MatchPlayer(match_id=match.match_id, player_id=player)
            matchplayer.seen(journal.start)
            db.session.add(matchplayer)

    journal.matches_updated = len(existing_matches)
    journal.matches_added = len(new_matches)


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
    ids = [player.player_id for player in players]

    # Load the stats
    # Using the cache here can fill up the redis backend with player data, so we skip it here.
    stats = {data["Guid"]: data for data in api_wrapper(lambda: get_api().get_user_stats(ids, cache_skip=True))}

    # Update players
    for player in players:
        if player.player_id in stats:
            player_stats = PlayerStats(player_id=player.player_id, snapshot_taken=update_time)
            player_stats.load_stats(stats[player.player_id])
            db.session.add(player_stats)

            player.latest_snapshot = player_stats.snapshot_taken
            db.session.add(player)


def update_player_regions(players):
    # Iterate through the players
    for player in players:
        # Detect most common region
        regions_query = db.session.query(Match.server_region, db.func.count(Match.server_region)).\
                                   join(MatchPlayer).\
                                   filter(MatchPlayer.player_id == player.player_id).\
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
    callsigns = api_wrapper(lambda: get_api().get_user_callsign([player.player_id for player in players], cache_skip=True))

    @CallsignConflictResolver(logger, callsigns)
    def update_callsigns(players, callsigns):
        # Iterate through the players
        count = 0
        for player in (player for player in players if player.player_id in callsigns and player.callsign != callsigns[player.player_id]):
            player.callsign = callsigns[player.player_id]
            db.session.add(player)
            count += 1

        return count

    return update_callsigns(players, callsigns)


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
                       filter(MatchPlayer.match_id == match.match_id).all()

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


def poll_servers(flags):
    # Prepare journal
    start = datetime.utcnow()
    journal = PollJournal.last()
    if journal is not None and journal.status in (PollStatus.in_progress, PollStatus.not_started):
        logger.error("Previous in-progress poll found! Refusing to start a new poll.")
        return journal
    else:
        journal = PollJournal(start=start, flags=flags, status=PollStatus.not_started, stage=PollStage.not_started)

    journal.status = PollStatus.in_progress
    db.session.add(journal)
    db.session.commit()

    try:
        with db.session.no_autoflush:
            # Load server list
            journal.stage_next(PollStage.fetch_servers)
            db.session.commit()
            players, matches = load_server_list(journal)

            # Update players
            journal.stage_next(PollStage.players)
            db.session.commit()
            update_seen_players(players, journal)

            # Update matches
            journal.stage_next(PollStage.matches)
            db.session.commit()
            update_seen_matches(matches, journal)

            # Complete
            journal.stage_next(PollStage.complete)
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


def update_tracker(flags):
    # Check for resume flag
    resume = UpdateFlag.resume in flags
    if resume:
        flags.remove(UpdateFlag.resume)

    # Prepare journal
    start = datetime.utcnow()
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
        # Get the start time from the last completed update
        last_journal = UpdateJournal.last_completed()
        if last_journal is None:
            last = None
        else:
            last = last_journal.start

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
