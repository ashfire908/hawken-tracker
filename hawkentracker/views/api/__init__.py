# -*- coding: utf-8 -*-
# Hawken Tracker - API

from flask import Blueprint, Response, json

api = Blueprint("data", __name__, url_prefix="/api")


def api_response(payload, status):
    return Response(response=json.dumps(payload), status=status, mimetype="application/json")

# Load submodules
from hawkentracker.views.api import data, ingester
