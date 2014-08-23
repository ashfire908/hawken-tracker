# -*- coding: utf-8 -*-
# Hawken Tracker - Config

import json
import os.path
from hawkentracker import app

# Define config defaults
app.config.update(
    DEBUG=False,
    SECRET_KEY="DevelopmentKey",
    EMAIL_TOKEN_MAX_AGE=172800,
    RESET_TOKEN_MAX_AGE=172800,
    SQLALCHEMY_DATABASE_URI=None,
    REDIS_URI=None,
    REDIS_PREFIX="hawkentracker",
    API_SCHEME="http",
    API_HOST=None,
    API_USER=None,
    API_PASS=None,
    API_ATTEMPTS=1,
    API_TIMEOUT=15,
    TRACKER_BATCH_SIZE=500,
    SITE_ADDRESS="http://localhost:5000",
    EMAIL_ADDRESS="localhost",
    EMAIL_SERVER=None,
    EMAIL_USER=None,
    EMAIL_PASS=None,
    SUPPORT_EMAIL=None,
    MATCH_STATS_THRESHOLD=2,
    RANK_PERCENT_THRESHOLD=0.01
)

# Load in config
with app.open_instance_resource(os.path.join(app.instance_path, "config.json"), mode="r") as f:
    app.config.update(json.load(f))
    if app.config["SQLALCHEMY_DATABASE_URI"] is None:
        raise ValueError("No database URI has been set")
    if app.config["REDIS_URI"] is None:
        raise ValueError("No Redis URI has been set")
    if app.config["API_USER"] is None:
        raise ValueError("No Hawken API user has been set")
    if app.config["API_PASS"] is None:
        raise ValueError("No Hawken API password has been set")
