# -*- coding: utf-8 -*-
# Hawken Tracker - Events Ingester

import logging
from datetime import datetime, timezone

from hawkentracker.database import Match, Player, db, MatchPlayer
from hawkentracker.interface import api_wrapper, get_api
from hawkentracker.tracker import CallsignConflictResolver
from hawkentracker.util import DEFAULT_GUID

logger = logging.getLogger(__name__)

event_ingesters = []


class EventIngester:
    def __init__(self, name, handler, filters=None):
        self.name = name
        self.handler = handler
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

                # TODO: Support other conditions besides equality
                if event_data != value:
                    return False
            except KeyError:
                return False

        return True

    def ingest(self, event):
        try:
            with db.session.no_autoflush:
                result = self.handler(event)

            db.session.commit()
            return result
        except:
            logger.exception("Handler {0} failed to ingest event".format(self.name))
            return False

    @staticmethod
    def register(name, filters=None):
        def decorator(func):
            event_ingesters.append(EventIngester(name, func, filters))
            return func

        return decorator


def handle_event(event):
    triggered = 0
    failed = 0

    for ingester in event_ingesters:
        if ingester.accepts(event):
            if not ingester.ingest(event):
                failed += 1
            triggered += 1

    return triggered, failed


# Match started/ended events
def match_parse_players(data):
    # Parse players
    active_players = {}
    for i in range(int(data["Num_Players"])):
        player_data = {k.split(".", 1)[-1]: v for k, v in data if k.startswith("Player%i" % i)}
        # Make sure it's not a bot
        if player_data["UserID"] != DEFAULT_GUID:
            active_players[player_data["UserID"]] = player_data

    inactive_players = {}
    for i in range(int(data["Num_Players_Inactive"])):
        player_data = {k.split(".", 1)[-1]: v for k, v in data if k.startswith("InactivePlayer%i" % i)}
        # Make sure it's not a bot
        if player_data["UserID"] != DEFAULT_GUID:
            inactive_players[player_data["UserID"]] = player_data

    players = set(list(active_players.keys()) + list(inactive_players.keys()))

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
            raise RuntimeError("Server info required to create match, but server cannot be found.")
        if server_info["MatchId"] != match_id:
            # Server has already moved to new match
            raise RuntimeError("Unable to create match from server info: Server is reporting a different match id")
        match = Match(match_id=match_id)
        match.load_server_info(server_info)


def match_update_players(players, event_time):
    existing_players = []
    for player in Player.query.filter(Player.player_id.in_(players)).all():
        existing_players.append(player.id)
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


@EventIngester.register("match_started", {"Verb": "Started", "Subject.Type": "Match", "Producer.Type": "HawkenGameServer"})
def match_started_event(event):
    match_id = event["Subject"]["Id"]
    server_id = event["Data"]["ServerListingGuid"]
    event_time = datetime.fromtimestamp(float(event["TimeCreated"]), timezone.utc)

    # Parse the players
    players, active_players, inactive_players = match_parse_players(event["Data"])

    # Mark match as seen and load event data
    match = get_or_create_match(match_id, server_id)
    match.seen(event_time)
    match.load_match_started(event["Data"])
    db.session.add(match)

    # Update players seen data
    match_update_players(players, event_time)

    # Get match players
    query = MatchPlayer.query.filter(MatchPlayer.match_id == match_id).filter(MatchPlayer.player_id.in_(players))
    match_players = {match_player.id: match_player for match_player in query.all()}

    # Update existing inactive players
    for match_player, data in ((match_players[guid], data) for guid, data in inactive_players.items() if guid in match_players):
        match_player.load_match_started(data, False)
        db.session.add(match_player)

    # Since we don't know when inactive players were in the match, we don't add them here.

    # Update existing active players
    for match_player, data in ((match_players[guid], data) for guid, data in active_players.items() if guid in match_players):
        match_player.seen(event_time)
        match_player.load_match_started(data, True)
        db.session.add(match_player)

    # Add new active players
    for guid, data in ((guid, data) for guid, data in active_players.items() if guid not in match_players):
        match_player = MatchPlayer(match_id=match_id, player_id=guid)
        match_player.seen(event_time)
        match_player.load_match_started(data, True)
        db.session.add(match_player)

    return True


@EventIngester.register("match_ended", {"Verb": "Ended", "Subject.Type": "Match", "Producer.Type": "HawkenGameServer"})
def match_ended_event(event):
    match_id = event["Subject"]["Id"]
    server_id = event["Data"]["ServerListingGuid"]
    event_time = datetime.fromtimestamp(float(event["TimeCreated"]), timezone.utc)

    # Parse the players
    players, active_players, inactive_players = match_parse_players(event["Data"])

    # Mark match as seen and load event data
    match = get_or_create_match(match_id, server_id)
    match.seen(event_time)
    match.load_match_ended(event["Data"])
    db.session.add(match)

    # Update players seen data
    match_update_players(players, event_time)

    # Get match players
    query = MatchPlayer.query.filter(MatchPlayer.match_id == match_id).filter(MatchPlayer.player_id.in_(players))
    match_players = {match_player.id: match_player for match_player in query.all()}

    # Update existing inactive players
    for match_player, data in ((match_players[guid], data) for guid, data in inactive_players.items() if guid in match_players):
        match_player.load_match_ended(data, False)
        db.session.add(match_player)

    # Since we don't know when inactive players were in the match, we don't add them here.

    # Update existing active players
    for match_player, data in ((match_players[guid], data) for guid, data in active_players.items() if guid in match_players):
        match_player.seen(event_time)
        match_player.load_match_ended(data, True)
        db.session.add(match_player)

    # Add new active players
    for guid, data in ((guid, data) for guid, data in active_players.items() if guid not in match_players):
        match_player = MatchPlayer(match_id=match_id, player_id=guid)
        match_player.seen(event_time)
        match_player.load_match_ended(data, True)
        db.session.add(match_player)

    return True
