# -*- coding: utf-8 -*-
# Hawken Tracker - Config

import os
import json
import logging

required_config = ("SQLALCHEMY_DATABASE_URI", "REDIS_URL", "HAWKEN_API_USER", "HAWKEN_API_PASS")
env_mapping = {}
log_levels = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0
}


class DefaultSettings:
    DEBUG = False
    SECRET_KEY = "DevelopmentKey"
    LOG_LEVEL = None
    LOG_FORMAT = "%(asctime)s %(message)s"
    EMAIL_TOKEN_MAX_AGE = 172800
    RESET_TOKEN_MAX_AGE = 172800
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = None
    REDIS_PREFIX = "hawkentracker"
    REDIS_SESSION_LIFETIME = 86400
    HAWKEN_API_SCHEME = None
    HAWKEN_API_HOST = None
    HAWKEN_API_USER = None
    HAWKEN_API_PASS = None
    HAWKEN_API_ATTEMPTS = 1
    HAWKEN_API_TIMEOUT = 15
    TRACKER_BATCH_SIZE = 500
    MATCH_STATS_THRESHOLD = 2
    RANK_PERCENT_THRESHOLD = 0.01
    USERNAME_MIN_LENGTH = 1
    USERNAME_MAX_LENGTH = 32
    PASSWORD_MIN_LENGTH = 1
    PASSWORD_MAX_LENGTH = 64


def parse_env_value(value):
    try:
        return json.loads(value)
    except ValueError:
        return value


def load_config(app, filename=None, parameters=None):
    env_prefix = app.name.upper() + "_"
    env_settings = env_prefix + "SETTINGS"

    # Load defaults
    app.config.from_object(DefaultSettings)

    # Load from file
    if filename is None:
        filename = os.getenv(env_settings, None)

        if filename is None:
            filename = os.path.join(app.instance_path, "config.json")

    try:
        with open(filename) as f:
            app.config.update(json.load(f))
    except FileNotFoundError:
        pass

    # Load from environment
    for key, value in os.environ.items():
        if key.startswith(env_prefix) and key != env_settings:
            app.config[key[len(env_prefix)]] = parse_env_value(value)
        elif key in env_mapping:
            app.config[env_mapping[key]] = parse_env_value(value)

    # Load from parameters
    if parameters is not None:
        app.config.update(parameters)

    # Check for required config
    for config in required_config:
        if config not in app.config or app.config[config] is None:
            raise ValueError("Config value {0} is required but was not specified".format(config))


def setup_logging(app):
    level = app.config.get("LOG_LEVEL", None)

    if level is not None and level.upper() in log_levels:
        level = log_levels[level.upper()]
    else:
        level = log_levels["NOTSET"]

    logging.basicConfig(format=app.config.get("LOG_FORMAT", None), level=level)
