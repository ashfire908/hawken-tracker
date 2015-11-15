# -*- coding: utf-8 -*-
# Hawken Tracker - Database Models

import statistics
from datetime import datetime

from sqlalchemy.dialects import postgres

from hawkentracker.database import db
from hawkentracker.database.util import NativeIntEnum, NativeStringEnum
from hawkentracker.mappings import UpdateStatus, UpdateStage, UpdateFlag

__all__ = ["Player", "PlayerStats", "Match", "MatchPlayer", "PollLog", "UpdateJournal"]


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

    matches = db.relationship("MatchPlayer", order_by="MatchPlayer.last_seen", backref=db.backref("player", uselist=False))
    stats = db.relationship("PlayerStats", uselist=False, order_by="PlayerStats.snapshot_taken")
    stats_history = db.relationship("PlayerStats", order_by="PlayerStats.snapshot_taken", backref=db.backref("player", uselist=False))

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
    pilot_level = db.Column(db.Integer, default=1, nullable=False, index=True)
    time_played = db.Column(db.Integer, default=0, nullable=False, index=True)
    xp = db.Column(db.Integer, index=True)
    xp_per_min = db.Column(db.Float, index=True)
    hc = db.Column(db.Integer, index=True)
    hc_per_min = db.Column(db.Float, index=True)
    kills = db.Column(db.Integer, default=0, nullable=False)
    deaths = db.Column(db.Integer, default=0, nullable=False)
    assists = db.Column(db.Integer, default=0, nullable=False)
    kda = db.Column(db.Float, index=True)
    kill_steals = db.Column(db.Integer, default=0, nullable=False)
    kill_steal_ratio = db.Column(db.Float, index=True)
    critical_assists = db.Column(db.Integer, default=0, nullable=False)
    critical_assist_ratio = db.Column(db.Float, index=True)
    damage_in = db.Column(db.Float, default=0, nullable=False)
    damage_out = db.Column(db.Float, default=0, nullable=False)
    damage_ratio = db.Column(db.Float, index=True)
    matches = db.Column(db.Integer, default=0, nullable=False)
    wins = db.Column(db.Integer, default=0, nullable=False)
    losses = db.Column(db.Integer, default=0, nullable=False)
    abandons = db.Column(db.Integer, default=0, nullable=False)
    win_loss = db.Column(db.Float, index=True)
    dm_total = db.Column(db.Integer, default=0, nullable=False)
    dm_win = db.Column(db.Integer, default=0, nullable=False)
    dm_mvp = db.Column(db.Integer, default=0, nullable=False)
    dm_loss = db.Column(db.Integer, default=0, nullable=False)
    dm_abandon = db.Column(db.Integer, default=0, nullable=False)
    dm_win_loss = db.Column(db.Float, index=True)
    tdm_total = db.Column(db.Integer, default=0, nullable=False)
    tdm_win = db.Column(db.Integer, default=0, nullable=False)
    tdm_loss = db.Column(db.Integer, default=0, nullable=False)
    tdm_abandon = db.Column(db.Integer, default=0, nullable=False)
    tdm_win_loss = db.Column(db.Float, index=True)
    ma_total = db.Column(db.Integer, default=0, nullable=False)
    ma_win = db.Column(db.Integer, default=0, nullable=False)
    ma_loss = db.Column(db.Integer, default=0, nullable=False)
    ma_abandon = db.Column(db.Integer, default=0, nullable=False)
    ma_win_loss = db.Column(db.Float, index=True)
    sg_total = db.Column(db.Integer, default=0, nullable=False)
    sg_win = db.Column(db.Integer, default=0, nullable=False)
    sg_loss = db.Column(db.Integer, default=0, nullable=False)
    sg_abandon = db.Column(db.Integer, default=0, nullable=False)
    sg_win_loss = db.Column(db.Float, index=True)
    coop_total = db.Column(db.Integer, default=0, nullable=False)
    coop_win = db.Column(db.Integer, default=0, nullable=False)
    coop_loss = db.Column(db.Integer, default=0, nullable=False)
    coop_abandon = db.Column(db.Integer, default=0, nullable=False)
    coop_win_loss = db.Column(db.Float, index=True)
    cooptdm_total = db.Column(db.Integer, default=0, nullable=False)
    cooptdm_win = db.Column(db.Integer, default=0, nullable=False)
    cooptdm_loss = db.Column(db.Integer, default=0, nullable=False)
    cooptdm_abandon = db.Column(db.Integer, default=0, nullable=False)
    cooptdm_win_loss = db.Column(db.Float, index=True)

    def __repr__(self):
        return "<PlayerStats(player_id='{0}', snapshot_taken={1})>".format(self.player_id, self.snapshot_taken)

    def load_stats(self, stats):
        # Filters
        default_mmr = (0.0, 1250.0, 1500.0)
        min_time = 36000  # 1 hour
        min_matches = 50
        min_kills = 100
        min_assists = 100

        # Unranked stats
        self.kills = stats.get("Kills.Total", 0)
        self.deaths = stats.get("Death.Total", 0)
        self.assists = stats.get("Assist.Total", 0)
        self.kill_steals = stats.get("Kills.Steal", 0)
        self.critical_assists = stats.get("Assist.CriticalDamage", 0)
        self.damage_in = stats.get("Damage.Sustained.Total", 0.0)
        self.damage_out = stats.get("Damage.Dealt.Total", 0.0)
        self.dm_total = stats.get("GameMode.DM.TotalMatches", 0)
        self.dm_win = stats.get("GameMode.DM.Wins", 0)
        self.dm_mvp = stats.get("GameMode.DM.MVP", 0)
        self.dm_loss = stats.get("GameMode.DM.Losses", 0)
        self.dm_abandon = stats.get("GameMode.DM.Abandonded", 0)
        self.tdm_total = stats.get("GameMode.TDM.TotalMatches", 0)
        self.tdm_win = stats.get("GameMode.TDM.Wins", 0)
        self.tdm_loss = stats.get("GameMode.TDM.Losses", 0)
        self.tdm_abandon = stats.get("GameMode.TDM.Abandonded", 0)
        self.ma_total = stats.get("GameMode.MA.TotalMatches", 0)
        self.ma_win = stats.get("GameMode.MA.Wins", 0)
        self.ma_loss = stats.get("GameMode.MA.Losses", 0)
        self.ma_abandon = stats.get("GameMode.MA.Abandonded", 0)
        self.sg_total = stats.get("GameMode.SG.TotalMatches", 0)
        self.sg_win = stats.get("GameMode.SG.Wins", 0)
        self.sg_loss = stats.get("GameMode.SG.Losses", 0)
        self.sg_abandon = stats.get("GameMode.SG.Abandonded", 0)
        self.coop_total = stats.get("GameMode.CoOp.TotalMatches", 0)
        self.coop_win = stats.get("GameMode.CoOp.Wins", 0)
        self.coop_loss = stats.get("GameMode.CoOp.Losses", 0)
        self.coop_abandon = stats.get("GameMode.CoOp.Abandonded", 0)
        self.cooptdm_total = stats.get("GameMode.CoOpTDM.TotalMatches", 0)
        self.cooptdm_win = stats.get("GameMode.CoOpTDM.Wins", 0)
        self.cooptdm_loss = stats.get("GameMode.CoOpTDM.Losses", 0)
        self.cooptdm_abandon = stats.get("GameMode.CoOpTDM.Abandonded", 0)
        self.matches = min(stats.get("GameMode.All.TotalMatches", 0) - self.cooptdm_total, 0)
        self.wins = min(stats.get("GameMode.All.Wins", 0) - self.cooptdm_win, 0)
        self.losses = min(stats.get("GameMode.All.Losses", 0) - self.cooptdm_loss, 0)
        self.abandons = min(stats.get("GameMode.All.Abandonded", 0) - self.cooptdm_abandon, 0)

        # Ranked stats
        mmr = stats.get("MatchMaking.Rating", 0.0)
        if mmr not in default_mmr:
            self.mmr = mmr

        self.pilot_level = stats.get("Progress.Pilot.Level", 1)
        self.time_played = stats.get("TimePlayed", 0)

        if self.time_played >= min_time:
            # XP
            xp = stats.get("ExpPoints", 0)
            if xp > 0:
                self.xp = xp
                self.xp_per_min = (self.xp / self.time_played) * 60

            # HC
            hc = stats.get("HawkenPoints", 0)
            if hc > 0:
                self.hc = hc
                self.hc_per_min = (self.hc / self.time_played) * 60

            # KDA
            if self.kills >= min_kills and self.deaths > 0 and self.assists >= min_assists:
                self.kda = (self.kills + self.assists) / self.deaths

            # Kill steals
            if self.kill_steals > 0 and self.kills >= min_kills:
                self.kill_steal_ratio = self.kill_steals / self.kills

            # Critical assists
            if self.critical_assists > 0 and self.assists >= min_assists:
                self.critical_assist_ratio = self.critical_assists / self.assists

            # Damage
            if self.damage_in > 0 and self.damage_out > 0:
                self.damage_ratio = self.damage_out / self.damage_in

            # Deathmatch
            if self.dm_total >= min_matches and self.dm_mvp > 0 and self.dm_loss + self.dm_abandon + (self.dm_win - self.dm_mvp) > 0:
                self.dm_win_loss = self.dm_mvp / (self.dm_loss + self.dm_abandon + (self.dm_win - self.dm_mvp))

            # Team Deathmatch
            if self.tdm_total >= min_matches and self.tdm_win > 0 and self.tdm_loss + self.tdm_abandon > 0:
                self.tdm_win_loss = self.tdm_win / (self.tdm_loss + self.tdm_abandon)

            # Missile Assault
            if self.ma_total >= min_matches and self.ma_win > 0 and self.ma_loss + self.ma_abandon > 0:
                self.ma_win_loss = self.ma_win / (self.ma_loss + self.ma_abandon)

            # Siege
            if self.sg_total >= min_matches and self.sg_win > 0 and (self.sg_loss + self.sg_abandon) > 0:
                self.sg_win_loss = self.sg_win / (self.sg_loss + self.sg_abandon)

            # COBD
            if self.coop_total >= min_matches and self.coop_win > 0 and self.coop_loss + self.coop_abandon > 0:
                self.coop_win_loss = self.coop_win / (self.coop_loss + self.coop_abandon)

            # Coop TDM
            if self.cooptdm_total >= min_matches and self.cooptdm_win > 0 and self.cooptdm_loss + self.cooptdm_abandon > 0:
                self.cooptdm_win_loss = self.cooptdm_win / (self.cooptdm_loss + self.cooptdm_abandon)

            # All
            if self.matches >= min_matches and self.wins > 0 and self.losses + self.abandons > 0:
                self.win_loss = self.wins / (self.losses + self.abandons)


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


class PollLog(db.Model):
    __tablename__ = "polls"

    time = db.Column(db.DateTime, primary_key=True)
    success = db.Column(db.Boolean, index=True, nullable=False)
    time_taken = db.Column(db.Float, nullable=False)
    players_found = db.Column(db.Integer)
    matches_found = db.Column(db.Integer)

    def __repr__(self):
        return "<PollLog(time={0}, success={1}, time_taken={2})>".format(self.time, self.success, self.time_taken)

    @staticmethod
    def last():
        last = db.session.query(PollLog.time).filter(PollLog.success.is_(True)).order_by(PollLog.time.desc()).first()
        if last is None:
            return None
        return last[0]

    @staticmethod
    def record(success, start, end, players, matches):
        poll = PollLog(time=start, success=success, time_taken=(end - start).total_seconds(), players_found=players, matches_found=matches)
        db.session.add(poll)


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
        return "<UpdateLog(start={0}, status={1}, stage={2})>".format(self.start, self.status, self.stage)

    @staticmethod
    def last():
        return db.session.query(UpdateJournal).order_by(UpdateJournal.start.desc()).first()

    @staticmethod
    def last_completed():
        last = db.session.query(UpdateJournal.start).filter(UpdateJournal.status == UpdateStatus.complete).order_by(UpdateJournal.start.desc()).first()
        if last is None:
            return None
        return last[0]
