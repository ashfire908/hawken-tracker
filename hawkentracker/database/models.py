# -*- coding: utf-8 -*-
# Hawken Tracker - Database Models

import statistics
from datetime import datetime

from sqlalchemy.dialects import postgres

from hawkentracker.database import db
from hawkentracker.database.util import NativeIntEnum, NativeStringEnum
from hawkentracker.mappings import PollFlag, PollStatus, PollStage, UpdateFlag, UpdateStatus, UpdateStage

__all__ = ["Player", "PlayerStats", "Match", "MatchPlayer", "PollJournal", "UpdateJournal"]


class Player(db.Model):
    __tablename__ = "players"
    __table_args__ = (
        db.Index("ix_players_callsign", db.func.lower("callsign"), unique=True),
    )

    player_id = db.Column(db.String(36), primary_key=True)
    callsign = db.Column(db.String)
    first_seen = db.Column(db.DateTime, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)
    common_region = db.Column(db.String)
    opt_out = db.Column(db.Boolean)
    blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    blacklist_reason = db.Column(db.String)
    latest_snapshot = db.Column(db.DateTime)

    matches = db.relationship(
        "MatchPlayer",
        order_by="MatchPlayer.last_seen",
        backref=db.backref("player", uselist=False)
    )
    stats = db.relationship(
        "PlayerStats",
        primaryjoin="and_(Player.player_id==PlayerStats.player_id, "
                    "Player.latest_snapshot==PlayerStats.snapshot_taken)",
        uselist=False
    )
    stats_history = db.relationship(
        "PlayerStats",
        order_by="PlayerStats.snapshot_taken",
        backref=db.backref("player", uselist=False)
    )

    def seen(self, seen_time):
        if self.first_seen is None or self.first_seen > seen_time:
            self.first_seen = seen_time
        if self.last_seen is None or self.last_seen < seen_time:
            self.last_seen = seen_time

    def __repr__(self):
        return "<Player(player_id='{0}')>".format(self.player_id)

    @staticmethod
    def by_callsign(callsign):
        return Player.query.filter(db.func.lower(Player.callsign) == callsign.lower()).first()


class PlayerStats(db.Model):
    __tablename__ = "player_stats"

    player_id = db.Column(db.String(36), db.ForeignKey("players.player_id"), primary_key=True, index=True)
    snapshot_taken = db.Column(db.DateTime, primary_key=True, index=True)
    mmr = db.Column(db.Float, index=True)
    pilot_level = db.Column(db.Integer)
    time_played = db.Column(db.Integer, index=True)
    xp = db.Column(db.Integer, index=True)
    xp_per_min = db.Column(db.Float, index=True)
    hc = db.Column(db.Integer, index=True)
    hc_per_min = db.Column(db.Float, index=True)
    kills = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    assists = db.Column(db.Integer)
    kda = db.Column(db.Float, index=True)
    kill_steals = db.Column(db.Integer)
    kill_steal_ratio = db.Column(db.Float, index=True)
    critical_assists = db.Column(db.Integer)
    critical_assist_ratio = db.Column(db.Float, index=True)
    damage_in = db.Column(db.Float)
    damage_out = db.Column(db.Float)
    damage_ratio = db.Column(db.Float, index=True)
    matches = db.Column(db.Integer)
    wins = db.Column(db.Integer)
    losses = db.Column(db.Integer)
    abandons = db.Column(db.Integer)
    win_loss = db.Column(db.Float, index=True)
    dm_total = db.Column(db.Integer)
    dm_win = db.Column(db.Integer)
    dm_mvp = db.Column(db.Integer)
    dm_loss = db.Column(db.Integer)
    dm_abandon = db.Column(db.Integer)
    dm_win_loss = db.Column(db.Float, index=True)
    tdm_total = db.Column(db.Integer)
    tdm_win = db.Column(db.Integer)
    tdm_loss = db.Column(db.Integer)
    tdm_abandon = db.Column(db.Integer)
    tdm_win_loss = db.Column(db.Float, index=True)
    ma_total = db.Column(db.Integer)
    ma_win = db.Column(db.Integer)
    ma_loss = db.Column(db.Integer)
    ma_abandon = db.Column(db.Integer)
    ma_win_loss = db.Column(db.Float, index=True)
    sg_total = db.Column(db.Integer)
    sg_win = db.Column(db.Integer)
    sg_loss = db.Column(db.Integer)
    sg_abandon = db.Column(db.Integer)
    sg_win_loss = db.Column(db.Float, index=True)
    coop_total = db.Column(db.Integer)
    coop_win = db.Column(db.Integer)
    coop_loss = db.Column(db.Integer)
    coop_abandon = db.Column(db.Integer)
    coop_win_loss = db.Column(db.Float, index=True)
    cooptdm_total = db.Column(db.Integer)
    cooptdm_win = db.Column(db.Integer)
    cooptdm_loss = db.Column(db.Integer)
    cooptdm_abandon = db.Column(db.Integer)
    cooptdm_win_loss = db.Column(db.Float, index=True)

    def __repr__(self):
        return "<PlayerStats(player_id='{0}', snapshot_taken={1})>".format(self.player_id, self.snapshot_taken)

    def load_stats(self, stats):
        def naz(value):
            """None as zero helper"""
            if value is None:
                return 0
            return value

        # Filters
        default_mmr = (0.0, 1250.0, 1500.0, None)
        min_time = 36000  # 1 hour
        min_matches = 50
        min_kills = 100
        min_assists = 100

        # Unranked stats
        self.kills = stats.get("Kills.Total")
        self.deaths = stats.get("Death.Total")
        self.assists = stats.get("Assist.Total")
        self.kill_steals = stats.get("Kills.Steal")
        self.critical_assists = stats.get("Assist.CriticalDamage")
        self.damage_in = stats.get("Damage.Sustained.Total")
        self.damage_out = stats.get("Damage.Dealt.Total")
        self.dm_total = stats.get("GameMode.DM.TotalMatches")
        self.dm_win = stats.get("GameMode.DM.Wins")
        self.dm_mvp = stats.get("GameMode.DM.MVP")
        self.dm_loss = stats.get("GameMode.DM.Losses")
        self.dm_abandon = stats.get("GameMode.DM.Abandonded")
        self.tdm_total = stats.get("GameMode.TDM.TotalMatches")
        self.tdm_win = stats.get("GameMode.TDM.Wins")
        self.tdm_loss = stats.get("GameMode.TDM.Losses")
        self.tdm_abandon = stats.get("GameMode.TDM.Abandonded")
        self.ma_total = stats.get("GameMode.MA.TotalMatches")
        self.ma_win = stats.get("GameMode.MA.Wins")
        self.ma_loss = stats.get("GameMode.MA.Losses")
        self.ma_abandon = stats.get("GameMode.MA.Abandonded")
        self.sg_total = stats.get("GameMode.SG.TotalMatches")
        self.sg_win = stats.get("GameMode.SG.Wins")
        self.sg_loss = stats.get("GameMode.SG.Losses")
        self.sg_abandon = stats.get("GameMode.SG.Abandonded")
        self.coop_total = stats.get("GameMode.CoOp.TotalMatches")
        self.coop_win = stats.get("GameMode.CoOp.Wins")
        self.coop_loss = stats.get("GameMode.CoOp.Losses")
        self.coop_abandon = stats.get("GameMode.CoOp.Abandonded")
        self.cooptdm_total = stats.get("GameMode.CoOpTDM.TotalMatches")
        self.cooptdm_win = stats.get("GameMode.CoOpTDM.Wins")
        self.cooptdm_loss = stats.get("GameMode.CoOpTDM.Losses")
        self.cooptdm_abandon = stats.get("GameMode.CoOpTDM.Abandonded")
        self.matches = stats.get("GameMode.All.TotalMatches")
        self.wins = stats.get("GameMode.All.Wins")
        self.losses = stats.get("GameMode.All.Losses")
        self.abandons = stats.get("GameMode.All.Abandonded")

        # Remove coop tdm from global counts
        if self.matches is not None and self.cooptdm_total is not None:
            self.matches -= self.cooptdm_total
        if self.wins is not None and self.cooptdm_win is not None:
            self.wins -= self.cooptdm_win
        if self.losses is not None and self.cooptdm_loss is not None:
            self.losses -= self.cooptdm_loss
        if self.abandons is not None and self.cooptdm_abandon is not None:
            self.abandons -= self.cooptdm_abandon

        # Ranked stats
        mmr = stats.get("MatchMaking.Rating")
        if mmr not in default_mmr:
            self.mmr = mmr

        self.pilot_level = stats.get("Progress.Pilot.Level")
        self.time_played = stats.get("TimePlayed")

        if self.time_played is not None and self.time_played >= min_time:
            # XP
            xp = stats.get("ExpPoints")
            if xp is not None and xp > 0:
                self.xp = xp
                self.xp_per_min = (self.xp / self.time_played) * 60

            # HC
            hc = stats.get("HawkenPoints")
            if hc is not None and hc > 0:
                self.hc = hc
                self.hc_per_min = (self.hc / self.time_played) * 60

            # KDA
            if None not in (self.kills, self.deaths, self.assists) and \
               self.kills >= min_kills and self.deaths > 0 and self.assists >= min_assists:
                self.kda = (self.kills + self.assists) / self.deaths

            # Kill steals
            if None not in (self.kill_steals, self.kills) and \
               self.kill_steals > 0 and self.kills >= min_kills:
                self.kill_steal_ratio = self.kill_steals / self.kills

            # Critical assists
            if None not in (self.critical_assists, self.assists) and \
               self.critical_assists > 0 and self.assists >= min_assists:
                self.critical_assist_ratio = self.critical_assists / self.assists

            # Damage
            if None not in (self.damage_in, self.damage_out) and \
               self.damage_in > 0 and self.damage_out > 0:
                self.damage_ratio = self.damage_out / self.damage_in

            # Deathmatch
            if None not in (self.dm_total, self.dm_mvp) and \
               self.dm_total >= min_matches and self.dm_mvp > 0:
                losses = naz(self.dm_loss) + naz(self.dm_abandon) + (naz(self.dm_win) - naz(self.dm_mvp))
                if losses > 0:
                    self.dm_win_loss = naz(self.dm_mvp) / losses

            # Team Deathmatch
            if None not in (self.tdm_total, self.tdm_win) and \
               self.tdm_total >= min_matches and self.tdm_win > 0:
                losses = naz(self.tdm_loss) + naz(self.tdm_abandon)
                if losses > 0:
                    self.tdm_win_loss = self.tdm_win / losses

            # Missile Assault
            if None not in (self.ma_total, self.ma_win) and \
               self.ma_total >= min_matches and self.ma_win > 0:
                losses = naz(self.ma_loss) + naz(self.ma_abandon)
                if losses > 0:
                    self.ma_win_loss = self.ma_win / losses

            # Siege
            if None not in (self.sg_total, self.sg_win) and \
               self.sg_total >= min_matches and self.sg_win > 0:
                losses = naz(self.sg_loss) + naz(self.sg_abandon)
                if losses > 0:
                    self.sg_win_loss = self.sg_win / losses

            # Coop Bot Destruction
            if None not in (self.coop_total, self.coop_win) and \
               self.coop_total >= min_matches and self.coop_win > 0:
                losses = naz(self.coop_loss) + naz(self.coop_abandon)
                if losses > 0:
                    self.coop_win_loss = self.coop_win / losses

            # Coop TDM
            if None not in (self.cooptdm_total, self.cooptdm_win) and \
               self.cooptdm_total >= min_matches and self.cooptdm_win > 0:
                losses = naz(self.cooptdm_loss) + naz(self.cooptdm_abandon)
                if losses > 0:
                    self.cooptdm_win_loss = self.cooptdm_win / losses

            # All
            if None not in (self.matches, self.wins) and \
               self.matches >= min_matches and self.wins > 0:
                losses = naz(self.losses) + naz(self.abandons)
                if losses > 0:
                    self.win_loss = self.wins / losses


class Match(db.Model):
    __tablename__ = "matches"

    match_id = db.Column(db.String(32), primary_key=True)
    server_name = db.Column(db.String, nullable=False)
    server_region = db.Column(db.String, nullable=False)
    server_gametype = db.Column(db.String, nullable=False)
    server_map = db.Column(db.String, nullable=False)
    server_version = db.Column(db.String, nullable=False)
    server_matchmaking = db.Column(db.Boolean)
    server_tournament = db.Column(db.Boolean)
    server_password_protected = db.Column(db.Boolean)
    server_mmr_ignored = db.Column(db.Boolean)
    first_seen = db.Column(db.DateTime, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)
    last_stats_update = db.Column(db.DateTime)
    pilot_level_avg = db.Column(db.Float)
    mmr_avg = db.Column(db.Float)
    mmr_min = db.Column(db.Float)
    mmr_max = db.Column(db.Float)
    mmr_stddev = db.Column(db.Float)

    players = db.relationship("MatchPlayer", order_by="MatchPlayer.last_seen", backref=db.backref("match", uselist=False))

    def __repr__(self):
        return "<Match(match_id='{0}', server_name='{1}')>".format(self.match_id, self.server_name)

    def seen(self, seen_time):
        if self.first_seen is None or self.first_seen > seen_time:
            self.first_seen = seen_time
        if self.last_seen is None or self.last_seen < seen_time:
            self.last_seen = seen_time

    def load_server_info(self, server):
        self.server_name = server["ServerName"]
        self.server_region = server["Region"]
        self.server_gametype = server["GameType"]
        self.server_map = server["Map"]
        self.server_version = server["GameVersion"]

        self.server_matchmaking = server["IsMatchmakingVisible"]
        self.server_tournament = server["DeveloperData"].get("bTournament", "false").lower() == "true"
        self.server_password_protected = len(server["DeveloperData"].get("PasswordHash", "")) > 0
        self.server_mmr_ignored = server["DeveloperData"].get("bIgnoreMMR", "FALSE").lower() == "true"

    def calculate_stats(self, mmrs, pilot_levels, update_time):
        # Update stats
        if len(mmrs) > 0:
            self.mmr_avg = statistics.mean(mmrs)
            self.mmr_min = min(mmrs)
            self.mmr_max = max(mmrs)
            if len(mmrs) > 1:
                self.mmr_stddev = statistics.stdev(mmrs)
        if len(pilot_levels) > 0:
            self.pilot_level_avg = statistics.mean(pilot_levels)

        self.last_stats_update = update_time


class MatchPlayer(db.Model):
    __tablename__ = "match_players"

    match_id = db.Column(db.String(32), db.ForeignKey("matches.match_id"), index=True, primary_key=True)
    player_id = db.Column(db.String(36), db.ForeignKey("players.player_id"), index=True, primary_key=True)
    first_seen = db.Column(db.DateTime, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<MatchPlayer(match_id='{0}', player_id='{1}')>".format(self.match_id, self.player_id)

    def seen(self, seen_time):
        if self.first_seen is None or self.first_seen > seen_time:
            self.first_seen = seen_time
        if self.last_seen is None or self.last_seen < seen_time:
            self.last_seen = seen_time


class PollJournal(db.Model):
    __tablename__ = "polls"

    start = db.Column(db.DateTime, primary_key=True)
    end = db.Column(db.DateTime)
    time_elapsed = db.Column(db.Float, default=0, nullable=False)
    status = db.Column(NativeIntEnum(PollStatus), default=PollStatus.not_started, index=True, nullable=False)
    stage = db.Column(NativeIntEnum(PollStage), default=PollStage.not_started, nullable=False)
    flags = db.Column(postgres.ARRAY(NativeStringEnum(PollFlag)), default=[], nullable=False)
    players_updated = db.Column(db.Integer)
    players_added = db.Column(db.Integer)
    matches_updated = db.Column(db.Integer)
    matches_added = db.Column(db.Integer)

    def stage_next(self, next_stage):
        self.stage = next_stage
        db.session.add(self)

    def fail(self, poll_start):
        now = datetime.utcnow()
        self.time_elapsed += (now - poll_start).total_seconds()
        self.end = now
        self.status = PollStatus.failed
        db.session.add(self)

    def complete(self, poll_start):
        now = datetime.utcnow()
        self.time_elapsed += (now - poll_start).total_seconds()
        self.end = now
        self.status = PollStatus.complete
        db.session.add(self)

    def __repr__(self):
        return "<PollJournal(start={0}, status={1}, stage={2})>".format(self.start, self.status, self.stage)

    @staticmethod
    def last():
        return db.session.query(PollJournal).order_by(PollJournal.start.desc()).first()

    @staticmethod
    def last_completed():
        return db.session.query(PollJournal).filter(PollJournal.status == PollStatus.complete).order_by(PollJournal.start.desc()).first()


class UpdateJournal(db.Model):
    __tablename__ = "updates"

    start = db.Column(db.DateTime, primary_key=True)
    end = db.Column(db.DateTime)
    time_elapsed = db.Column(db.Float, default=0, nullable=False)
    status = db.Column(NativeIntEnum(UpdateStatus), default=UpdateStatus.not_started, index=True, nullable=False)
    stage = db.Column(NativeIntEnum(UpdateStage), default=UpdateStage.not_started, nullable=False)
    current_step = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer, default=0)
    flags = db.Column(postgres.ARRAY(NativeStringEnum(UpdateFlag)), default=[], nullable=False)
    players_updated = db.Column(db.Integer, default=0, nullable=False)
    matches_updated = db.Column(db.Integer, default=0, nullable=False)
    callsigns_updated = db.Column(db.Integer, default=0, nullable=False)
    global_rankings_updated = db.Column(db.Boolean, default=False, nullable=False)

    def stage_start(self, total):
        if self.current_step is None:
            self.current_step = 0
        self.total_steps = total
        db.session.add(self)
        return self.current_step

    @property
    def stage_progress(self):
        if self.current_step is None or self.total_steps is None:
            return None

        if self.total_steps == 0:
            return 0

        return (self.current_step / self.total_steps) * 100

    def stage_checkpoint(self, current):
        self.current_step = current
        db.session.add(self)

    def stage_next(self, next_stage):
        self.current_step = None
        self.total_steps = None
        self.stage = next_stage
        db.session.add(self)

    def fail(self, update_start):
        now = datetime.utcnow()
        self.time_elapsed += (now - update_start).total_seconds()
        self.end = now
        self.status = UpdateStatus.failed
        db.session.add(self)

    def complete(self, update_start):
        now = datetime.utcnow()
        self.time_elapsed += (now - update_start).total_seconds()
        self.end = now
        self.status = UpdateStatus.complete
        self.current_step = None
        self.total_steps = None
        db.session.add(self)

    def __repr__(self):
        return "<UpdateJournal(start={0}, status={1}, stage={2})>".format(self.start, self.status, self.stage)

    @staticmethod
    def last():
        return db.session.query(UpdateJournal).order_by(UpdateJournal.start.desc()).first()

    @staticmethod
    def last_completed():
        return db.session.query(UpdateJournal).filter(UpdateJournal.status == UpdateStatus.complete).order_by(UpdateJournal.start.desc()).first()
