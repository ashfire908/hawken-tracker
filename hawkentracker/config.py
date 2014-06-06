# -*- coding: utf-8 -*-
# Hawken Tracker - Config

import json
import os.path
from hawkentracker import app

# Define config defaults
app.config.update(
    DEBUG=False,
    SECRET_KEY="DevelopmentKey",
    SQLALCHEMY_DATABASE_URI=None,
    REDIS_URI=None,
    REDIS_PREFIX="hawkentracker",
    API_SCHEME="http",
    API_HOST=None,
    API_USER=None,
    API_PASS=None,
    API_ATTEMPTS=1,
    API_TIMEOUT=15
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
    if app.config["API_ATTEMPTS"] is None:
        raise ValueError("No Hawken API attempts limit has been set")