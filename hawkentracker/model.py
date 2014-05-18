# -*- coding: utf-8 -*-
# Hawken Tracker - DB Models

from sqlalchemy import Column, ForeignKey, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    id = Column(String(36), primary_key=True)
    first_seen = Column("firstseen", DateTime, nullable=False)
    last_seen = Column("lastseen", DateTime, nullable=False)
    callsign = Column(String)

    matches = relationship("MatchPlayer", order_by="MatchPlayer.match_id", backref="players")

    def __repr__(self):
        return "<Player(id='{0}', callsign='{1}')>".format(self.id, self.callsign)

    def update(self, poll_time):
        if self.first_seen is None:
            self.first_seen = poll_time
        self.last_seen = poll_time


class PlayerStats(Base):
    __tablename__ = "playerstats"

    player_id = Column("playerid", String(36), ForeignKey("players.id"), primary_key=True)
    last_updated = Column("lastupdated", DateTime, nullable=False)
    mmr = Column(Float, nullable=False)
    pilot_level = Column("pilotlevel", Integer, nullable=False)
    time_played = Column("timeplayed", Integer, nullable=False)
    experience = Column("experience", Integer, nullable=False)
    kills = Column(Integer, nullable=False)
    deaths = Column(Integer, nullable=False)
    assists = Column(Integer, nullable=False)
    total_matches = Column("totalmatches", Integer)
    total_wins = Column("totalwins", Integer)
    total_losses = Column("totallosses", Integer)
    total_abandons = Column("totalabandons", Integer)
    tdm_matches = Column("tdmmatches", Integer)
    tdm_wins = Column("tdmwins", Integer)
    tdm_losses = Column("tdmlosses", Integer)
    dm_matches = Column("dmmatches", Integer)
    dm_wins = Column("dmwins", Integer)
    dm_losses = Column("dmlosses", Integer)
    sg_matches = Column("sgmatches", Integer)
    sg_wins = Column("sgwins", Integer)
    sg_losses = Column("sglosses", Integer)
    ma_matches = Column("mamatches", Integer)
    ma_wins = Column("mawins", Integer)
    ma_losses = Column("malosses", Integer)
    coop_matches = Column("coopmatches", Integer)
    coop_wins = Column("coopwins", Integer)
    coop_losses = Column("cooplosses", Integer)
    cooptdm_matches = Column("cooptdmmatches", Integer)
    cooptdm_wins = Column("cooptdmwins", Integer)
    cooptdm_losses = Column("cooptdmlosses", Integer)

    player = relationship("Player", backref="playerstats")

    def __repr__(self):
        return "<PlayerStats(player_id='{0}', mmr={1}, pilot_level={2})>".format(self.player_id, self.mmr, self.pilot_level)

    def update(self, stats, update_time):
        self.mmr = stats.get("MatchMaking.Rating", 0.0)
        self.pilot_level = stats.get("Progress.Pilot.Level", 0)
        self.time_played = stats.get("TimePlayed", 0)
        self.experience = stats.get("ExpPoints", 0)
        self.kills = stats.get("Kills.Total", 0)
        self.deaths = stats.get("Death.Total", 0)
        self.assists = stats.get("Assist.Total", 0)
        self.total_matches = stats.get("GameMode.All.TotalMatches", None)
        self.total_wins = stats.get("GameMode.All.Wins", None)
        self.total_losses = stats.get("GameMode.All.Losses", None)
        self.total_abandons = stats.get("GameMode.All.Abandonded", None)
        self.tdm_matches = stats.get("GameMode.TDM.TotalMatches", None)
        self.tdm_wins = stats.get("GameMode.TDM.Wins", None)
        self.tdm_losses = stats.get("GameMode.TDM.Losses", None)
        self.dm_matches = stats.get("GameMode.DM.TotalMatches", None)
        self.dm_wins = stats.get("GameMode.DM.Wins", None)
        self.dm_losses = stats.get("GameMode.DM.Losses", None)
        self.sg_matches = stats.get("GameMode.SG.TotalMatches", None)
        self.sg_wins = stats.get("GameMode.SG.Wins", None)
        self.sg_losses = stats.get("GameMode.SG.Losses", None)
        self.ma_matches = stats.get("GameMode.MA.TotalMatches", None)
        self.ma_wins = stats.get("GameMode.MA.Wins", None)
        self.ma_losses = stats.get("GameMode.MA.Losses", None)
        self.coop_matches = stats.get("GameMode.CoOp.TotalMatches", None)
        self.coop_wins = stats.get("GameMode.CoOp.Wins", None)
        self.coop_losses = stats.get("GameMode.CoOp.Losses", None)
        self.cooptdm_matches = stats.get("GameMode.CoOpTDM.TotalMatches", None)
        self.cooptdm_wins = stats.get("GameMode.CoOpTDM.Wins", None)
        self.cooptdm_losses = stats.get("GameMode.CoOpTDM.Losses", None)

        self.last_updated = update_time


class Match(Base):
    __tablename__ = "matches"

    id = Column(String(32), primary_key=True)
    server_name = Column("servername", String, nullable=False)
    server_region = Column("serverregion", String, nullable=False)
    server_gametype = Column("servergametype", String, nullable=False)
    server_map = Column("servermap", String, nullable=False)
    server_version = Column("serverversion", String, nullable=False)
    first_seen = Column("firstseen", DateTime, nullable=False)
    last_seen = Column("lastseen", DateTime, nullable=False)

    players = relationship("MatchPlayer", order_by="MatchPlayer.player_id", backref="matches")

    def __repr__(self):
        return "<Match(id='{0}', server_name='{1}')>".format(self.id, self.server_name)

    def update(self, server, poll_time):
        self.server_name = server["ServerName"]
        self.server_region = server["Region"]
        self.server_gametype = server["GameType"]
        self.server_map = server["Map"]
        self.server_version = server["GameVersion"]

        if self.first_seen is None:
            self.first_seen = poll_time
        self.last_seen = poll_time


class MatchPlayer(Base):
    __tablename__ = "matchplayers"

    match_id = Column("matchid", String(32), ForeignKey("matches.id"), primary_key=True)
    player_id = Column("playerid", String(36), ForeignKey("players.id"), primary_key=True)
    first_seen = Column("firstseen", DateTime, nullable=False)
    last_seen = Column("lastseen", DateTime, nullable=False)

    match = relationship("Match", backref="matchplayers")
    player = relationship("Player", backref="players")

    def __repr__(self):
        return "<MatchPlayer(match_id='{0}', player_id='{1}')>".format(self.match_id, self.player_id)

    def update(self, poll_time):
        if self.first_seen is None:
            self.first_seen = poll_time
        self.last_seen = poll_time


class PollLog(Base):
    __tablename__ = "polls"

    time = Column(DateTime, primary_key=True)
    success = Column(Boolean, nullable=False)
    time_taken = Column("timetaken", Float, nullable=False)

    def __repr__(self):
        return "<PollLog(update={0}, success={1}, time_taken={2})>".format(self.update, self.success, self.time_taken)


class UpdateLog(Base):
    __tablename__ = "updates"

    time = Column(DateTime, primary_key=True)
    success = Column(Boolean, nullable=False)
    time_taken = Column("timetaken", Float, nullable=False)

    def __repr__(self):
        return "<UpdateLog(update={0}, success={1}, time_taken={2})>".format(self.update, self.success, self.time_taken)
