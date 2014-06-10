# -*- coding: utf-8 -*-
# Hawken Tracker - API-related helpers

from redis import StrictRedis
from flask import g
from requests.exceptions import HTTPError, Timeout
from hawkenapi.cache import Cache
from hawkenapi.client import Client
from hawkenapi.exceptions import ServiceUnavailable
from hawkenapi.interface import Session
from hawkentracker import app


class InterfaceException(Exception):
    pass


def format_redis_key(*args):
    return app.config["REDIS_PREFIX"] + ":" + ":".join(args)


def get_redis():
    session = g.get("redis_session", None)
    if session is None:
        session = StrictRedis.from_url(url=app.config["REDIS_URI"])
        g.redis_session = session

    return session


def get_api():
    client = g.get("api_client", None)
    if client is None:
        # Set up the client
        client = Client(session=Session(host=app.config["API_HOST"], scheme=app.config["API_SCHEME"], timeout=app.config["API_TIMEOUT"]))
        client.cache = Cache("hawkenapi", url=app.config["REDIS_URI"])

        redis = get_redis()
        token = redis.get(format_redis_key("api_token"))
        if token:
            # Restore cached state
            client.grant = token.decode()
            client.identifier = app.config["API_USER"]
            client.password = app.config["API_PASS"]
        else:
            # Login to the API
            api_wrapper(lambda: client.login(app.config["API_USER"], app.config["API_PASS"]))
            redis.set(format_redis_key("api_token"), client.grant.token)

    return client


def api_wrapper(func):
    last_exception = None
    for x in range(0, app.config.get("API_ATTEMPTS")):
        try:
            return func()
        except (ServiceUnavailable, HTTPError, Timeout) as e:
            last_exception = e

    raise InterfaceException from last_exception


@app.teardown_appcontext
def teardown_api(exception):
    client = g.get("api_client", None)
    if client is not None and client.authed:
        redis = get_redis()
        redis.set(format_redis_key("api_token"), client.grant.token)
