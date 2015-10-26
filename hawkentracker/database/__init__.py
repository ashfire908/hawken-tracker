# -*- coding: utf-8 -*-
# Hawken Tracker - Database

import logging

from flask.ext.sqlalchemy import SQLAlchemy

# Init DB
logger = logging.getLogger(__name__)
db = SQLAlchemy()

# Import models
from hawkentracker.database.models import *
