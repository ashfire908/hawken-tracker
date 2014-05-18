# -*- coding: utf-8 -*-
# Hawken Tracker

import logging
import time
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from hawkenapi.client import Client
from hawkentracker.model import Base, Player, PlayerStats, Match, MatchPlayer, PollLog, UpdateLog


class HawkenTracker:
    def __init__(self, url, username, password, debug=False):
        self.debug = debug
        if self.debug:
            logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)

        self._client = Client()
        self._username = username
        self._password = password

    @property
    def client(self):
        if not self._client.authed:
            self._client.login(self._username, self._password)

        return self._client

    @contextmanager
    def get_session(self, callback=None):
        success = True
        session = self.Session()
        try:
            begin = datetime.now()
            start = time.time()
            yield session
            session.commit()
            end = time.time()
        except:
            session.rollback()
            end = time.time()
            success = False
            raise
        finally:
            try:
                if callback is not None:
                    callback(session, success, begin, end - start)
            finally:
                session.close()

    def setup_db(self):
        Base.metadata.create_all(self.engine, checkfirst=True)

    def last_poll(self, session):
        last = session.query(PollLog.time).filter(PollLog.success == True).order_by(PollLog.time.desc()).first()
        if last:
            return last[0]
        else:
            return last

    def last_update(self, session):
        last = session.query(UpdateLog.time).filter(UpdateLog.success == True).order_by(UpdateLog.time.desc()).first()
        if last:
            return last[0]
        else:
            return last

    def record_poll(self, session, success, start, duration):
        poll = PollLog(time=start, success=success, time_taken=duration)
        session.add(poll)
        session.commit()

    def record_update(self, session, success, start, duration):
        update = UpdateLog(time=start, success=success, time_taken=duration)
        session.add(update)
        session.commit()

    def update_players(self, session, players, poll_time):
        # Update existing players
        found = []
        for player in session.query(Player).filter(Player.id.in_(players)):
            found.append(player.id)
            player.update(poll_time)
            session.add(player)

        # Add new players
        for guid in (guid for guid in players if guid not in found):
            player = Player(id=guid)
            player.update(poll_time)
            session.add(player)

    def update_matches(self, session, matches, poll_time):
        # Update existing matches
        found = []
        for match in session.query(Match).filter(Match.id.in_(matches.keys())):
            found.append(match.id)
            match.update(matches[match.id], poll_time)
            session.add(match)

            # Update match players
            if len(matches[match.id]["Users"]) > 0:
                self.update_match_players(session, match.id, matches[match.id]["Users"], poll_time)

        # Add new matches
        for matchid in (matchid for matchid in matches.keys() if matchid not in found):
            match = Match(id=matchid)
            match.update(matches[matchid], poll_time)
            session.add(match)

            # Add match players
            if len(matches[matchid]["Users"]) > 0:
                self.add_match_players(session, matchid, matches[matchid]["Users"], poll_time)

    def add_match_players(self, session, match, players, poll_time):
        # Add new players
        for player in players:
            matchplayer = MatchPlayer(match_id=match, player_id=player)
            matchplayer.update(poll_time)
            session.add(matchplayer)

    def update_match_players(self, session, match, players, poll_time):
        # Update existing players
        found = []
        for matchplayer in session.query(MatchPlayer).filter(MatchPlayer.match_id == match, MatchPlayer.player_id.in_(players)):
            found.append(matchplayer.player_id)
            matchplayer.update(poll_time)
            session.add(matchplayer)

        # Add new players
        for player in (player for player in players if player not in found):
            matchplayer = MatchPlayer(match_id=match, player_id=player)
            matchplayer.update(poll_time)
            session.add(matchplayer)

    def update_player_stats(self, session, players, stats, update_time):
        # Update existing players
        found = []
        for playerstats in session.query(PlayerStats).filter(PlayerStats.player_id.in_(players)):
            found.append(playerstats.player_id)
            playerstats.update(stats[playerstats.player_id], update_time)
            session.add(playerstats)

        # Add new players
        for player in (player for player in players if player not in found):
            playerstats = PlayerStats(player_id=player)
            playerstats.update(stats[player], update_time)
            session.add(playerstats)

    def poll_players(self):
        with self.get_session(callback=self.record_poll) as session:
            # Get the server list data
            poll_time = datetime.now()
            server_list = self.client.get_server_list()

            players = set()
            for server in server_list:
                for player in server["Users"]:
                    players.add(player)
            matches = {server["MatchId"]: server for server in server_list if server["MatchId"] is not None}

            # Update data
            self.update_players(session, players, poll_time)
            self.update_matches(session, matches, poll_time)

            return len(players), len(matches)

    def stats_update(self):
        with self.get_session(callback=self.record_update) as session:
            # Get the list of players to update
            last_update = self.last_update(session)
            if last_update is None:
                players = [data[0] for data in session.query(Player.id).all()]
            else:
                players = [data[0] for data in session.query(Player.id).filter(Player.last_seen > last_update).all()]

            if len(players) > 0:
                # Load the player stats
                # Grab some coffee, this is gonna be a long one
                update_time = datetime.now()
                stats = {data["Guid"]: data for data in self.client.get_user_stats(players)}

                # Update data
                self.update_player_stats(session, players, stats, update_time)

            return len(players)
