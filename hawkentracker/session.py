# -*- coding: utf-8 -*-
# Hawken Tracker - Session

from uuid import uuid4

import msgpack
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface, SessionMixin

from hawkentracker.interface import create_redis_session, format_redis_key


class RedisSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True

        CallbackDict.__init__(self, initial, on_update)

        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    def __init__(self):
        self.redis = create_redis_session()
        self.prefix = "session"

    def generate_sid(self):
        return str(uuid4())

    def get_redis_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime

        return app.config["REDIS_SESSION_LIFETIME"]

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            return RedisSession(sid=sid, new=True)

        data = self.redis.get(format_redis_key(self.prefix, sid))

        if data is None:
            return RedisSession(sid=sid, new=True)

        return RedisSession(msgpack.unpackb(data, encoding="utf-8"), sid=sid)

    def save_session(self, app, session, response):
        key = format_redis_key(self.prefix, session.sid)
        domain = self.get_cookie_domain(app)

        if not session:
            self.redis.delete(key)
            if session.modified:
                response.delete_cookie(app.session_cookie_name, domain=domain)
        else:
            secure = self.get_cookie_secure(app)
            httponly = self.get_cookie_httponly(app)

            data = msgpack.packb(dict(session))

            redis_exp = self.get_redis_expiration_time(app, session)
            self.redis.setex(key, redis_exp, data)

            cookie_exp = self.get_expiration_time(app, session)
            response.set_cookie(app.session_cookie_name, session.sid, expires=cookie_exp, domain=domain, secure=secure,
                                httponly=httponly)
