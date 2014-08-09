# -*- coding: utf-8 -*-
# Hawken Tracker - External service helpers

import logging
import smtplib
from email.mime.text import MIMEText
from redis import StrictRedis
from flask import g
from requests.exceptions import HTTPError, Timeout
from hawkenapi.util import verify_guid
from hawkenapi.cache import Cache
from hawkenapi.client import Client
from hawkenapi.exceptions import ServiceUnavailable
from hawkenapi.interface import Session
from hawkentracker import app

logger = logging.getLogger(__name__)


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

        g.api_client = client

    return client


def api_wrapper(func):
    last_exception = None
    for x in range(0, app.config.get("API_ATTEMPTS")):
        if last_exception is not None:
            logger.warn("[API] Retrying failed call: {0} {1} ".format(type(last_exception), last_exception))
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


def send_email(to, subject, message):
    # Create the message
    message = MIMEText(message)
    message["Subject"] = subject
    message["From"] = app.config["EMAIL_ADDRESS"]
    message["To"] = to

    # Send the email
    connection = smtplib.SMTP(app.config["EMAIL_SERVER"])
    connection.sendmail(app.config["EMAIL_ADDRESS"], to, message.as_string())
    connection.quit()


def get_player_id(player, callsign=True):
    api = get_api()

    # Get the target player and their callsign
    if verify_guid(player):
        guid = player
        callsign = api.get_user_callsign(guid) if callsign else None
    else:
        guid = api.get_user_guid(player)
        callsign = api.get_user_callsign(guid) if callsign and guid is not None else None

    return guid, callsign
