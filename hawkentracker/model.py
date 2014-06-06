# -*- coding: utf-8 -*-
# Hawken Tracker - DB Models

from flask.ext.sqlalchemy import SQLAlchemy
from hawkentracker import app
from hawkentracker.mappings import Role, ListingPrivacy, JoinPrivacy, Confirmation

db = SQLAlchemy(app)


class NativeIntEnum(db.TypeDecorator):
    """Converts between a native enum and a database integer"""
    impl = db.Integer

    def __init__(self, enum):
        self.enum = enum
        super().__init__()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum(value)


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.String(36), primary_key=True)
    first_seen = db.Column(db.DateTime, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)
    home_region = db.Column(db.String)
    common_region = db.Column(db.String)
    opt_out = db.Column(db.Boolean, default=False, nullable=False)
    leaderboard_privacy = db.Column(NativeIntEnum(Role))
    rank_privacy = db.Column(NativeIntEnum(Role))
    stats_privacy = db.Column(NativeIntEnum(Role))
    match_privacy = db.Column(NativeIntEnum(Role))

    matches = db.relationship("MatchPlayer", order_by="MatchPlayer.last_seen", backref=db.backref("player", uselist=False))
    stats = db.relationship("PlayerStats", uselist=False, backref=db.backref("player", uselist=False))
    user = db.relationship("User", uselist=False, backref=db.backref("player", uselist=False))
    groups = db.relationship("GroupPlayer", backref=db.backref("player", uselist=False))

    def __repr__(self):
        return "<Player(id='{0}')>".format(self.id)

    def update(self, poll_time):
        if self.first_seen is None:
            self.first_seen = poll_time
        self.last_seen = poll_time


class PlayerStats(db.Model):
    __tablename__ = "playerstats"

    player_id = db.Column(db.String(36), db.ForeignKey("players.id"), primary_key=True)
    last_updated = db.Column(db.DateTime, nullable=False)
    mmr = db.Column(db.Float, default=0.0, nullable=False)
    pilot_level = db.Column(db.Integer, default=1, nullable=False)
    time_played = db.Column(db.Integer, default=0, nullable=False)
    xp_per_min = db.Column(db.Float)
    hc_per_min = db.Column(db.Float)
    kda = db.Column(db.Float)
    kill_steals = db.Column(db.Float)
    critical_assists = db.Column(db.Float)
    damage = db.Column(db.Float)
    win_loss = db.Column(db.Float)
    dm_win_loss = db.Column(db.Float)
    tdm_win_loss = db.Column(db.Float)
    ma_win_loss = db.Column(db.Float)
    sg_win_loss = db.Column(db.Float)
    coop_win_loss = db.Column(db.Float)
    cooptdm_win_loss = db.Column(db.Float)

    def __repr__(self):
        return "<PlayerStats(player_id='{0}', mmr={1}, pilot_level={2}, time_played={3})>".format(self.player_id, self.mmr, self.pilot_level, self.time_played)

    def update(self, stats, update_time):
        self.mmr = stats.get("MatchMaking.Rating", 0.0)
        self.pilot_level = stats.get("Progress.Pilot.Level", 1)
        self.time_played = stats.get("TimePlayed", 0)
        xp = stats.get("ExpPoints", 0)
        if xp > 0 and self.time_played > 0:
            self.xp_per_min = (xp / self.time_played) * 60
        hc = stats.get("HawkenPoints", 0)
        if hc > 0 and self.time_played > 0:
            self.hc_per_min = (hc / self.time_played) * 60
        kills = stats.get("Kills.Total", 0)
        deaths = stats.get("Death.Total", 0)
        assists = stats.get("Assist.Total", 0)
        if kills > 0 and deaths > 0 and assists > 0:
            self.kda = (kills + assists) / deaths
        kill_steals = stats.get("Kills.Steal", 0)
        if kill_steals > 0 and kills > 0:
            self.kill_steals = kill_steals / kills
        critical_assists = stats.get("Assist.CriticalDamage", 0)
        if critical_assists > 0 and assists > 0:
            self.critical_assists = critical_assists / assists
        damage_in = stats.get("Damage.Sustained.Total", 0)
        damage_out = stats.get("Damage.Dealt.Total", 0)
        if damage_in > 0 and damage_out > 0:
            self.damage = damage_out / damage_in
        all_win = stats.get("GameMode.All.Wins", 0)
        all_loss = stats.get("GameMode.All.Losses", 0)
        all_abandon = stats.get("GameMode.All.Abandonded", 0)
        if all_win > 0 and all_loss + all_abandon > 0:
            self.win_loss = all_win / (all_loss + all_abandon)
        dm_win = stats.get("GameMode.DM.Wins", 0)
        dm_loss = stats.get("GameMode.DM.Losses", 0)
        dm_abandon = stats.get("GameMode.DM.Abandonded", 0)
        if dm_win > 0 and dm_loss + dm_abandon > 0:
            self.dm_win_loss = dm_win / (dm_loss + dm_abandon)
        tdm_win = stats.get("GameMode.TDM.Wins", 0)
        tdm_loss = stats.get("GameMode.TDM.Losses", 0)
        tdm_abandon = stats.get("GameMode.TDM.Abandonded", 0)
        if tdm_win > 0 and tdm_loss + tdm_abandon > 0:
            self.tdm_win_loss = tdm_win / (tdm_loss + tdm_abandon)
        ma_win = stats.get("GameMode.MA.Wins", 0)
        ma_loss = stats.get("GameMode.MA.Losses", 0)
        ma_abandon = stats.get("GameMode.MA.Abandonded", 0)
        if ma_win > 0 and ma_loss + ma_abandon > 0:
            self.ma_win_loss = ma_win / (ma_loss + ma_abandon)
        sg_win = stats.get("GameMode.SG.Wins", 0)
        sg_loss = stats.get("GameMode.SG.Losses", 0)
        sg_abandon = stats.get("GameMode.SG.Abandonded", 0)
        if sg_win > 0 and (sg_loss + sg_abandon) > 0:
            self.sg_win_loss = sg_win / (sg_loss + sg_abandon)
        coop_win = stats.get("GameMode.CoOp.Wins", 0)
        coop_loss = stats.get("GameMode.CoOp.Losses", 0)
        coop_abandon = stats.get("GameMode.CoOp.Abandonded", 0)
        if coop_win > 0 and coop_loss + coop_abandon > 0:
            self.coop_win_loss = coop_win / (coop_loss + coop_abandon)
        cooptdm_win = stats.get("GameMode.CoOpTDM.Wins", 0)
        cooptdm_loss = stats.get("GameMode.CoOpTDM.Losses", 0)
        cooptdm_abandon = stats.get("GameMode.CoOpTDM.Abandonded", 0)
        if cooptdm_win > 0 and cooptdm_loss + cooptdm_abandon > 0:
            self.cooptdm_win_loss = cooptdm_win / (cooptdm_loss + cooptdm_abandon)

        self.last_updated = update_time


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    creation = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String, nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    email_confirm_expires = db.Column(db.DateTime)
    email_confirm_token = db.Column(db.String)
    type = db.Column(NativeIntEnum(Role), nullable=False)
    associated_player = db.Column(db.String(36), db.ForeignKey("players.id"))

    def __repr__(self):
        return "<User(id={0}, username='{1}')>".format(self.id, self.username)


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.String(32), primary_key=True)
    server_name = db.Column(db.String, nullable=False)
    server_region = db.Column(db.String, nullable=False)
    server_gametype = db.Column(db.String, nullable=False)
    server_map = db.Column(db.String, nullable=False)
    server_version = db.Column(db.String, nullable=False)
    first_seen = db.Column(db.DateTime, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)
    average_mmr = db.Column(db.Float)
    average_level = db.Column(db.Float)

    players = db.relationship("MatchPlayer", order_by="MatchPlayer.last_seen", backref=db.backref("match", uselist=False))

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


class MatchPlayer(db.Model):
    __tablename__ = "matchplayers"

    match_id = db.Column(db.String(32), db.ForeignKey("matches.id"), primary_key=True)
    player_id = db.Column(db.String(36), db.ForeignKey("players.id"), primary_key=True)
    first_seen = db.Column(db.DateTime, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<MatchPlayer(match_id='{0}', player_id='{1}')>".format(self.match_id, self.player_id)

    def update(self, poll_time):
        if self.first_seen is None:
            self.first_seen = poll_time
        self.last_seen = poll_time


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.Text)
    website = db.Column(db.String)
    invite_only = db.Column(db.Boolean, nullable=False)
    listing_privacy = db.Column(NativeIntEnum(ListingPrivacy), nullable=False)
    join_privacy = db.Column(NativeIntEnum(JoinPrivacy), nullable=False)
    group_privacy = db.Column(NativeIntEnum(Role), nullable=False)
    rank_privacy = db.Column(NativeIntEnum(Role), nullable=False)
    stats_privacy = db.Column(NativeIntEnum(Role), nullable=False)
    match_privacy = db.Column(NativeIntEnum(Role), nullable=False)

    players = db.relationship("GroupPlayer", backref=db.backref("group", uselist=False))

    def __repr__(self):
        return "<Group(id={0}, name='{1}')>".format(self.id, self.name)


class GroupPlayer(db.Model):
    __tablename__ = "groupplayers"

    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), primary_key=True)
    player_id = db.Column(db.String(36), db.ForeignKey("players.id"), primary_key=True)
    role = db.Column(NativeIntEnum(Role), nullable=False)
    confirmation = db.Column(NativeIntEnum(Confirmation), nullable=False)
    rank_privacy = db.Column(NativeIntEnum(Role))
    stats_privacy = db.Column(NativeIntEnum(Role))
    match_privacy = db.Column(NativeIntEnum(Role))

    def __repr__(self):
        return "<GroupPlayer(group_id='{0}', player_id='{1}')>".format(self.group_id, self.player_id)


class PollLog(db.Model):
    __tablename__ = "polls"

    time = db.Column(db.DateTime, primary_key=True)
    success = db.Column(db.Boolean, nullable=False)
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


class UpdateLog(db.Model):
    __tablename__ = "updates"

    time = db.Column(db.DateTime, primary_key=True)
    success = db.Column(db.Boolean, nullable=False)
    time_taken = db.Column(db.Float, nullable=False)
    players_updated = db.Column(db.Integer, nullable=False)
    matches_updated = db.Column(db.Integer, nullable=False)
    rankings_updated = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return "<UpdateLog(time={0}, success={1}, time_taken={2})>".format(self.time, self.success, self.time_taken)

    @staticmethod
    def last():
        last = db.session.query(UpdateLog.time).filter(UpdateLog.success.is_(True)).order_by(UpdateLog.time.desc()).first()
        if last is None:
            return None
        return last[0]

    @staticmethod
    def record(success, start, end, players, matches, rankings):
        update = UpdateLog(time=start, success=success, time_taken=(end - start).total_seconds(), players_updated=players, matches_updated=matches, rankings_updated=rankings)
        db.session.add(update)
