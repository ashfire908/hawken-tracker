# -*- coding: utf-8 -*-
# Hawken Tracker - Events Ingester

import sys
import logging
import itertools
import traceback
from datetime import datetime

from hawkentracker.database import Match, Player, db, MatchPlayer
from hawkentracker.exceptions import ServerNotFound
from hawkentracker.interface import api_wrapper, get_api
from hawkentracker.mappings import IngesterStatus
from hawkentracker.tracker import CallsignConflictResolver
from hawkentracker.util import DEFAULT_GUID

logger = logging.getLogger(__name__)


class EventIngester:
    ingesters = []

    def __init__(self, name, ingester, filters=None):
        self.name = name
        self.ingester = ingester
        self.filters = filters

    def accepts(self, event):
        if self.filters is None:
            return True

        for key, value in self.filters.items():
            path = key.split(".")
            try:
                event_data = event
                while len(path) > 0:
                    event_data = event_data[path.pop(0)]

                if isinstance(value, tuple):
                    # List of acceptable values
                    if event_data not in value:
                        return False
                else:
                    # Direct comparison
                    if event_data != value:
                        return False
            except KeyError:
                return False

        return True

    def ingest(self, event):
        try:
            with db.session.no_autoflush:
                result = self.ingester(event)

            db.session.commit()

            if not isinstance(result, dict) or "status" not in result or result["status"] == IngesterStatus.unset:
                logger.warn("Malformed result from ingester '{0}'.".format(self.name))
        except:
            logger.exception("Ingester '{0}' failed to ingest event.".format(self.name))

            exc_type, exc_value, exc_tb = sys.exc_info()

            tb_list = itertools.chain.from_iterable(line.rstrip().split("\n") for line in traceback.format_tb(exc_tb))

            result = {
                "status": IngesterStatus.error,
                "exception": traceback.format_exception_only(exc_type, exc_value)[0].rstrip(),
                "traceback": [line[2:] for line in tb_list]
            }

        return result

    @staticmethod
    def register(name, filters=None):
        def decorator(func):
            if name in (ingester.name for ingester in EventIngester.ingesters):
                raise ValueError("Ingester already registered with name '{0}'".format(name))
            EventIngester.ingesters.append(EventIngester(name, func, filters))
            return func

        return decorator

    @staticmethod
    def process_event(event):
        result = {
            "triggered": 0,
            "processed": 0,
            "failed": 0,
            "ingesters": {}
        }

        for ingester in EventIngester.ingesters:
            if ingester.accepts(event):
                ingest_result = ingester.ingest(event)

                # Update response
                result["triggered"] += 1
                if ingest_result["status"] == IngesterStatus.processed:
                    result["processed"] += 1
                elif ingest_result["status"] in (IngesterStatus.failed, IngesterStatus.error):
                    result["failed"] += 1

                result["ingesters"][ingester.name] = ingest_result

        return result

    @staticmethod
    def new_result():
        return {"status": IngesterStatus.unset}


# Match started/ended events
def match_parse_players(data):
    bots_as_players = 0

    # Parse players
    active_players = {}
    for i in range(12):
        player_data = {k.split(".", 1)[1]: v for k, v in data.items() if k.startswith("Player%i." % i)}
        # Make sure we found a player
        if not player_data:
            continue

        # Make sure it's not a bot
        if player_data["UserID"] != DEFAULT_GUID:
            active_players[player_data["UserID"]] = player_data
        else:
            bots_as_players += 1

    inactive_players = {}
    for i in range(12):
        player_data = {k.split(".", 1)[1]: v for k, v in data.items() if k.startswith("InactivePlayer%i." % i)}
        # Make sure we found a player
        if not player_data:
            continue

        # Make sure it's not a bot
        if player_data["UserID"] != DEFAULT_GUID:
            inactive_players[player_data["UserID"]] = player_data

    players = set(list(active_players.keys()) + list(inactive_players.keys()))

    # Calculate our own player/bot counts
    data["Num_Players"] = str(len(active_players))
    data["Num_Players_Inactive"] = str(len(inactive_players))
    data["Num_Bots"] = str(bots_as_players)

    return players, active_players, inactive_players


def get_or_create_match(match_id, server_id):
    # Get the match
    match = Match.query.get(match_id)

    # Create the match if it does not exist
    if match is None:
        # Load server info
        server_info = api_wrapper(lambda: get_api().get_server(server_id, cache_skip=True))
        if server_info is None:
            # Server info required to create match
            raise ServerNotFound(server_id)
        if server_info["MatchId"] != match_id:
            # Server has already moved to new match
            raise ServerNotFound(server_id, match_id=match_id)
        match = Match(match_id=match_id)
        match.load_server_info(server_info)
    elif match.server_id == DEFAULT_GUID:
        # Backfill server id
        match.server_id = server_id

    return match


def match_update_players(players, event_time):
    existing_players = []
    for player in Player.query.filter(Player.player_id.in_(players)).all():
        existing_players.append(player.player_id)
        player.seen(event_time)
        db.session.add(player)

    new_players = list(players.difference(existing_players))
    if len(new_players) > 0:
        # Load callsigns
        callsigns = api_wrapper(lambda: get_api().get_user_callsign(new_players, cache_skip=True))

        @CallsignConflictResolver(logger, callsigns)
        def add_players(players, callsigns):
            # Add new players
            for guid in players:
                player = Player(player_id=guid)
                player.callsign = callsigns.get(guid, None)
                player.seen(event_time)
                db.session.add(player)

        add_players(new_players, callsigns)


@EventIngester.register("match_start_end", {"Verb": ("Started", "Ended"), "Subject.Type": "Match", "Producer.Type": "HawkenGameServer"})
def match_start_end_event(event):
    result = EventIngester.new_result()

    match_id = event["Subject"]["Id"]
    match_started = event["Verb"] == "Started"
    server_id = event["Data"]["ServerListingGuid"]
    event_time = datetime.utcfromtimestamp(float(event["Data"]["TimeCreated"]))

    # Load match
    try:
        match = get_or_create_match(match_id, server_id)
    except ServerNotFound as e:
        result["status"] = IngesterStatus.failed
        if e.match_id is None:
            result["message"] = "Cannot ingest: Match not yet seen and could not find server"
        else:
            result["message"] = "Cannot ingest: Match not yet seen and server has different match"
        return result

    if (match_started and match.match_started is not None) or (not match_started and match.match_ended is not None):
        # Don't replay events
        logger.warn("Already ingested match start/end event, skipping... [Match {0}]".format(match_id))
        result["status"] = IngesterStatus.skipped
        result["message"] = "Event already ingested for '{0}'".format(match_id)
        return result

    # Set match status
    if db.inspect(match).transient:
        result["match_status"] = "created"
    else:
        result["match_status"] = "updated"

    # Parse the players
    players, active_players, inactive_players = match_parse_players(event["Data"])

    # Mark match as seen and load event data
    match.seen(event_time)
    if match_started:
        match.load_match_started(event["Data"])
    else:
        match.load_match_ended(event["Data"])
    db.session.add(match)

    # Update players seen data
    match_update_players(players, event_time)

    # Get match players
    query = MatchPlayer.query.filter(MatchPlayer.match_id == match_id).filter(MatchPlayer.player_id.in_(players))
    match_players = {match_player.player_id: match_player for match_player in query.all()}

    # Update existing inactive players
    for match_player, data in ((match_players[guid], data) for guid, data in inactive_players.items() if guid in match_players):
        if match_started:
            match_player.load_match_started(data, False)
        else:
            match_player.load_match_ended(data, False)
        db.session.add(match_player)

    # Since we don't know when inactive players were in the match, we don't add them here.

    # Update existing active players
    for match_player, data in ((match_players[guid], data) for guid, data in active_players.items() if guid in match_players):
        match_player.seen(event_time)
        if match_started:
            match_player.load_match_started(data, True)
        else:
            match_player.load_match_ended(data, True)
        db.session.add(match_player)

    # Add new active players
    for guid, data in ((guid, data) for guid, data in active_players.items() if guid not in match_players):
        match_player = MatchPlayer(match_id=match_id, player_id=guid)
        match_player.seen(event_time)
        if match_started:
            match_player.load_match_started(data, True)
        else:
            match_player.load_match_ended(data, True)
        db.session.add(match_player)

    result["status"] = IngesterStatus.processed
    if match_started:
        result["message"] = "Processed match started event"
    else:
        result["message"] = "Processed match ended event"
    return result
