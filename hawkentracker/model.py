# -*- coding: utf-8 -*-
# Hawken Tracker - DB Models

from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import event
from flask import current_app
from flask.ext.sqlalchemy import SQLAlchemy, get_debug_queries
from hawkentracker.mappings import LinkStatus, CoreRole
from hawkentracker.util import email_re, random_hex

db = SQLAlchemy()
pwd_context = CryptContext(schemes=["sha256_crypt"])


class TokenExpired(ValueError):
    pass


class TokenInvalid(ValueError):
    pass


def dump_queries(name):
    with open("queries-{0}".format(name), "w") as out:
        for query in get_debug_queries():
            out.write("-- Query ({0:.3f}s)\n{1}\nStatement: {2}\n".format(query.duration, query.context, query.statement))
            if isinstance(query.parameters, dict):
                for k, v in sorted(query.parameters.items()):
                    if isinstance(v, str):
                        v = "'" + v + "'"
                    out.write("Param: {0} = {1}\n".format(k, v))
            else:
                for item in query.parameters:
                    out.write("Param: {0}\n".format(item))


def column_windows(session, column, windowsize, *conditions):
    """Return a series of WHERE clauses against
    a given column that break it into windows.

    Result is an iterable of tuples, consisting of
    ((start, end), whereclause), where (start, end) are the ids.

    Requires a database that supports window functions,
    i.e. Postgresql, SQL Server, Oracle."""
    def int_for_range(start_id, end_id):
        if end_id:
            return db.and_(column >= start_id, column < end_id)
        else:
            return column >= start_id

    q = session.query(column, db.func.row_number().over(order_by=column).label("rownum")).from_self(column)

    if windowsize > 1:
        q = q.filter("rownum %% %d=1" % windowsize)

    for condition in conditions:
        q = q.filter(condition)

    intervals = [id for id, in q]

    while intervals:
        start = intervals.pop(0)
        if intervals:
            end = intervals[0]
        else:
            end = None
        yield int_for_range(start, end)


def windowed_query(q, column, windowsize, *conditions, streaming=True):
    """"Break a Query into windows on a given column."""

    for whereclause in column_windows(q.session, column, windowsize, *conditions):
        if streaming:
            for row in q.filter(whereclause).order_by(column):
                yield row
        else:
            yield q.filter(whereclause).order_by(column).all()


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
    link_user = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    link_status = db.Column(NativeIntEnum(LinkStatus), default=LinkStatus.none, nullable=False)
    opt_out = db.Column(db.Boolean, default=False, nullable=False)
    blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    blacklist_reason = db.Column(db.String)
    blacklist_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    view_privacy = db.Column(db.Integer)
    region_privacy = db.Column(db.Integer)
    leaderboard_privacy = db.Column(db.Integer)
    ranking_privacy = db.Column(db.Integer)
    ranked_stats_privacy = db.Column(db.Integer)
    overall_stats_privacy = db.Column(db.Integer)
    mech_stats_privacy = db.Column(db.Integer)
    match_list_privacy = db.Column(db.Integer)
    match_view_privacy = db.Column(db.Integer)
    group_privacy = db.Column(db.Integer)
    link_privacy = db.Column(db.Integer)

    matches = db.relationship("MatchPlayer", order_by="MatchPlayer.last_seen", backref=db.backref("player", uselist=False))
    stats = db.relationship("PlayerStats", uselist=False, backref=db.backref("player", uselist=False))
    user = db.relationship("User", foreign_keys=[link_user], uselist=False, backref="players")
    blacklister = db.relationship("User", foreign_keys=[blacklist_by])

    def __repr__(self):
        return "<Player(id='{0}')>".format(self.id)

    def update(self, poll_time):
        if self.first_seen is None:
            self.first_seen = poll_time
        self.last_seen = poll_time

    def link(self, user):
        self.link_user = user.id
        self.link_status = LinkStatus.linked

    def unlink(self):
        self.link_user = None
        self.link_status = LinkStatus.none


class PlayerStats(db.Model):
    __tablename__ = "player_stats"

    player_id = db.Column(db.String(36), db.ForeignKey("players.id"), primary_key=True)
    last_updated = db.Column(db.DateTime, nullable=False)
    mmr = db.Column(db.Float, index=True)
    pilot_level = db.Column(db.Integer, default=1, nullable=False, index=True)
    time_played = db.Column(db.Integer, default=0, nullable=False, index=True)
    xp = db.Column(db.Integer, index=True)
    xp_per_min = db.Column(db.Float, index=True)
    hc = db.Column(db.Integer, index=True)
    hc_per_min = db.Column(db.Float, index=True)
    kda = db.Column(db.Float, index=True)
    kill_steals = db.Column(db.Float, index=True)
    critical_assists = db.Column(db.Float, index=True)
    damage = db.Column(db.Float, index=True)
    win_loss = db.Column(db.Float, index=True)
    dm_win_loss = db.Column(db.Float, index=True)
    tdm_win_loss = db.Column(db.Float, index=True)
    ma_win_loss = db.Column(db.Float, index=True)
    sg_win_loss = db.Column(db.Float, index=True)
    coop_win_loss = db.Column(db.Float, index=True)
    cooptdm_win_loss = db.Column(db.Float, index=True)

    def __repr__(self):
        return "<PlayerStats(player_id='{0}', mmr={1}, pilot_level={2}, time_played={3})>".format(self.player_id, self.mmr, self.pilot_level, self.time_played)

    def update(self, stats, update_time):
        # Filters
        default_mmr = (0.0, 1250.0, 1500.0)
        min_time = 36000  # 1 hour
        min_matches = 50
        min_kills = 100
        min_assists = 100

        mmr = stats.get("MatchMaking.Rating", 0.0)
        # Ignore default mmrs
        if mmr not in default_mmr:
            self.mmr = mmr
        self.pilot_level = stats.get("Progress.Pilot.Level", 1)
        self.time_played = stats.get("TimePlayed", 0)

        if self.time_played >= min_time:
            xp = stats.get("ExpPoints", 0)
            if xp > 0:
                self.xp = xp
                self.xp_per_min = (xp / self.time_played) * 60
            hc = stats.get("HawkenPoints", 0)
            if hc > 0:
                self.hc = hc
                self.hc_per_min = (hc / self.time_played) * 60
            kills = stats.get("Kills.Total", 0)
            deaths = stats.get("Death.Total", 0)
            assists = stats.get("Assist.Total", 0)
            if kills >= min_kills and deaths > 0 and assists >= min_assists:
                self.kda = (kills + assists) / deaths
            kill_steals = stats.get("Kills.Steal", 0)
            if kill_steals > 0 and kills >= min_kills:
                self.kill_steals = kill_steals / kills
            critical_assists = stats.get("Assist.CriticalDamage", 0)
            if critical_assists > 0 and assists >= min_assists:
                self.critical_assists = critical_assists / assists
            damage_in = stats.get("Damage.Sustained.Total", 0)
            damage_out = stats.get("Damage.Dealt.Total", 0)
            if damage_in > 0 and damage_out > 0:
                self.damage = damage_out / damage_in
            dm_total = stats.get("GameMode.DM.TotalMatches", 0)
            dm_win = stats.get("GameMode.DM.Wins", 0)
            dm_mvp = stats.get("GameMode.DM.MVP", 0)
            dm_loss = stats.get("GameMode.DM.Losses", 0)
            dm_abandon = stats.get("GameMode.DM.Abandonded", 0)
            if dm_total >= min_matches and dm_mvp > 0 and dm_loss + dm_abandon + (dm_win - dm_mvp) > 0:
                self.dm_win_loss = dm_mvp / (dm_loss + dm_abandon + (dm_win - dm_mvp))
            tdm_total = stats.get("GameMode.TDM.TotalMatches", 0)
            tdm_win = stats.get("GameMode.TDM.Wins", 0)
            tdm_loss = stats.get("GameMode.TDM.Losses", 0)
            tdm_abandon = stats.get("GameMode.TDM.Abandonded", 0)
            if tdm_total >= min_matches and tdm_win > 0 and tdm_loss + tdm_abandon > 0:
                self.tdm_win_loss = tdm_win / (tdm_loss + tdm_abandon)
            ma_total = stats.get("GameMode.MA.TotalMatches", 0)
            ma_win = stats.get("GameMode.MA.Wins", 0)
            ma_loss = stats.get("GameMode.MA.Losses", 0)
            ma_abandon = stats.get("GameMode.MA.Abandonded", 0)
            if ma_total >= min_matches and ma_win > 0 and ma_loss + ma_abandon > 0:
                self.ma_win_loss = ma_win / (ma_loss + ma_abandon)
            sg_total = stats.get("GameMode.SG.TotalMatches", 0)
            sg_win = stats.get("GameMode.SG.Wins", 0)
            sg_loss = stats.get("GameMode.SG.Losses", 0)
            sg_abandon = stats.get("GameMode.SG.Abandonded", 0)
            if sg_total >= min_matches and sg_win > 0 and (sg_loss + sg_abandon) > 0:
                self.sg_win_loss = sg_win / (sg_loss + sg_abandon)
            coop_total = stats.get("GameMode.CoOp.TotalMatches", 0)
            coop_win = stats.get("GameMode.CoOp.Wins", 0)
            coop_loss = stats.get("GameMode.CoOp.Losses", 0)
            coop_abandon = stats.get("GameMode.CoOp.Abandonded", 0)
            if coop_total >= min_matches and coop_win > 0 and coop_loss + coop_abandon > 0:
                self.coop_win_loss = coop_win / (coop_loss + coop_abandon)
            cooptdm_total = stats.get("GameMode.CoOpTDM.TotalMatches", 0)
            cooptdm_win = stats.get("GameMode.CoOpTDM.Wins", 0)
            cooptdm_loss = stats.get("GameMode.CoOpTDM.Losses", 0)
            cooptdm_abandon = stats.get("GameMode.CoOpTDM.Abandonded", 0)
            if cooptdm_total >= min_matches and cooptdm_win > 0 and cooptdm_loss + cooptdm_abandon > 0:
                self.cooptdm_win_loss = cooptdm_win / (cooptdm_loss + cooptdm_abandon)
            all_total = stats.get("GameMode.All.TotalMatches", 0) - cooptdm_total
            all_win = stats.get("GameMode.All.Wins", 0) - cooptdm_win
            all_loss = stats.get("GameMode.All.Losses", 0) - cooptdm_loss
            all_abandon = stats.get("GameMode.All.Abandonded", 0) - cooptdm_abandon
            if all_total >= min_matches and all_win > 0 and all_loss + all_abandon > 0:
                self.win_loss = all_win / (all_loss + all_abandon)

        self.last_updated = update_time


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
    __tablename__ = "match_players"

    match_id = db.Column(db.String(32), db.ForeignKey("matches.id"), index=True, primary_key=True)
    player_id = db.Column(db.String(36), db.ForeignKey("players.id"), index=True, primary_key=True)
    first_seen = db.Column(db.DateTime, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<MatchPlayer(match_id='{0}', player_id='{1}')>".format(self.match_id, self.player_id)

    def update(self, poll_time):
        if self.first_seen is None:
            self.first_seen = poll_time
        self.last_seen = poll_time


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (db.UniqueConstraint("email", "email_confirmation_for"), )

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    creation = db.Column(db.DateTime, default=datetime.now, nullable=False)
    locked = db.Column(db.Boolean, default=False, nullable=False)
    lock_reason = db.Column(db.String)
    lock_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    confirmed_at = db.Column(db.DateTime)
    email_confirmation_for = db.Column(db.String)
    email_confirmation_token = db.Column(db.String)
    email_confirmation_sent_at = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String)
    password_reset_sent_at = db.Column(db.DateTime)
    role_id = db.Column(db.Integer, db.ForeignKey("user_roles.id"), nullable=False)
    view_privacy = db.Column(db.Integer)
    link_privacy = db.Column(db.Integer)

    @property
    def linked_players(self):
        return [player.id for player in self.players if player.link_status == LinkStatus.linked]

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def generate_email_confirmation(self, email):
        if email == self.email:
            # Initial confirmation
            self.email_confirmation_for = None
        else:
            self.email_confirmation_for = email
        self.email_confirmation_token = random_hex(16)
        self.email_confirmation_sent_at = datetime.now()

        return self.email_confirmation_token

    def verify_email_confirmation(self, email, token):
        if not (self.email_confirmation_for is None and not self.confirmed) or self.email_confirmation_token != token:
            raise TokenInvalid

        if self.email_confirmation_sent_at is None:
            raise TokenExpired

        delta = (datetime.now() - self.email_confirmation_sent_at).total_seconds()

        if delta > current_app.config["EMAIL_TOKEN_MAX_AGE"]:
            raise TokenExpired

        self.confirmed = True
        self.confirmed_at = datetime.now()

        self.email_confirmation_for = None
        self.email_confirmation_token = None
        self.email_confirmation_sent_at = None

        # Autopromote user
        if self.role == CoreRole.unconfirmed.value:
            self.role = CoreRole.user.value

    def generate_password_reset_token(self):
        self.password_reset_token = random_hex(16)
        self.password_reset_sent_at = datetime.now()

        return self.password_reset_token

    def verify_password_reset(self, token):
        if self.password_reset_token != token:
            raise TokenInvalid

        if self.password_reset_sent_at is None:
            raise TokenExpired

        delta = (datetime.now() - self.password_reset_sent_at).total_seconds()

        if delta > current_app.config["RESET_TOKEN_MAX_AGE"]:
            raise TokenExpired

        return True

    def set_password(self, new_password):
        self.password = new_password

        self.password_reset_token = None
        self.password_reset_sent_at = None

    def reset_password(self, token, new_password):
        if self.verify_password_reset(token):
            self.set_password(new_password)

    @db.validates("username")
    def validate_username(self, key, username):
        assert len(username) >= current_app.config.get("USERNAME_MIN_LENGTH", 1)
        assert "@" not in username
        return username

    @db.validates("password")
    def validate_password(self, key, password):
        assert len(password) >= current_app.config.get("PASSWORD_MIN_LENGTH", 1)
        return pwd_context.encrypt(password)

    @db.validates("email")
    def validate_email(self, key, email):
        assert email_re.match(email) is not None
        assert self.email_confirmation_for != email
        return email

    @db.validates("email_confirmation_for")
    def validate_email_confirmation_for(self, key, email):
        if email is not None:
            assert email_re.match(email) is not None
            assert self.email != email
        return email

    def is_authenticated(self):
        return True

    def is_active(self):
        return not self.locked

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return "<User(id={0}, username='{1}')>".format(self.id, self.username)

    @staticmethod
    def by_username(username):
        return User.query.filter(db.func.lower(User.username) == username.lower()).first()

    @staticmethod
    def by_email(email):
        return User.query.filter(db.func.lower(User.email) == email.lower()).first()
    
    @staticmethod
    def by_pending_email(email):
        return User.query.filter(db.func.lower(User.email_confirmation_for) == email.lower()).first()


#@event.listens_for(User, "before_delete")
#def unlink_players_on_user_delete(mapper, connection, target):
#    # Do stuff to unlink the connected players
#    Player.query.filter(Player.link_user == id).update({Player.link_status: LinkStatus.none, Player.link_user: None})


class AnonymousUser:
    id = "anon"
    username = None
    email = None
    password = None
    creation = None
    locked = False
    lock_reason = None
    lock_by = None
    confirmed = False
    confirmed_at = None
    email_confirmation_for = None
    email_confirmation_token = None
    email_confirmation_sent_at = None
    password_reset_token = None
    password_reset_sent_at = None
    role_id = CoreRole.anonymous.value
    view_privacy = 100
    link_privacy = 100

    @property
    def role_id(self):
        return CoreRole.anonymous.value

    @property
    def role(self):
        return UserRole.query.get(self.role_id)

    @property
    def players(self):
        return []

    @property
    def linked_players(self):
        return self.players

    def verify_password(self, password):
        raise NotImplementedError("Anonymous users cannot be modified")

    def generate_email_confirmation(self, email):
        raise NotImplementedError("Anonymous users cannot be modified")

    def verify_email_confirmation(self, email, token):
        raise NotImplementedError("Anonymous users cannot be modified")

    def generate_password_reset_token(self):
        raise NotImplementedError("Anonymous users cannot be modified")

    def verify_password_reset(self, token):
        raise NotImplementedError("Anonymous users cannot be modified")

    def set_password(self, new_password):
        raise NotImplementedError("Anonymous users cannot be modified")

    def reset_password(self, token, new_password):
        raise NotImplementedError("Anonymous users cannot be modified")

    def is_authenticated(self):
        return False

    def is_active(self):
        return not self.locked

    def is_anonymous(self):
        return True

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return "<AnonymousUser>"


class UserRole(db.Model):
    __tablename__ = "user_roles"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    superadmin = db.Column(db.Boolean, nullable=False)

    users = db.relationship("User", backref=db.backref("role", uselist=False))
    permissions = db.relationship("UserPermission", backref=db.backref("role", uselist=False))

    def __repr__(self):
        return "<UserRole(id={0}, name='{1}')>".format(self.id, self.name)


class UserPermission(db.Model):
    __tablename__ = "user_permissions"

    role_id = db.Column(db.Integer, db.ForeignKey("user_roles.id"), primary_key=True, index=True)
    permission = db.Column(db.String, primary_key=True)
    power = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<UserPermission(role_id={0}, permission='{1}', power={2})>".format(self.role_id, self.permission, self.power)


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


class UpdateLog(db.Model):
    __tablename__ = "updates"

    time = db.Column(db.DateTime, primary_key=True)
    success = db.Column(db.Boolean, index=True, nullable=False)
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
