# -*- coding: utf-8 -*-
# Hawken Tracker - Ingester views

from functools import wraps

from flask import request, current_app
from requests import codes as status_codes

from hawkentracker.events import EventIngester
from hawkentracker.views.api import api, api_response


def ingester_endpoint(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # Get config
        ingest_user = current_app.config["INGEST_USER"]
        ingest_pass = current_app.config["INGEST_PASS"]

        # Check authorization
        if ingest_user is not None and ingest_pass is not None:
            if request.authorization is None:
                return api_response({"error": "auth required"}, status_codes.unauthorized)

            http_auth = request.authorization

            if http_auth["username"] != ingest_user or http_auth["password"] != ingest_pass:
                return api_response({"error": "invalid auth"}, status_codes.unauthorized)

        # Run wrapped function
        return func(*args, **kwargs)
    return decorated_function


@api.route("/ingest", methods=["POST"])
@ingester_endpoint
def events_ingester():
    # Parse payload
    payload = request.get_json()

    # Validate payload as an event
    if not EventIngester.validate_event(payload):
        return api_response({"error": "invalid payload"}, status_codes.bad_request)

    # Run event handlers
    result = EventIngester.process_event(payload)

    # Return result
    if result["failed"] > 0:
        status_code = status_codes.internal_server_error
    else:
        status_code = status_codes.ok

    return api_response(result, status_code)
