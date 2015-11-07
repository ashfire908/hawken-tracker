# -*- coding: utf-8 -*-
# Hawken Tracker - Ingester views

from flask import request
from requests import codes as status_codes

from hawkentracker.events import EventIngester
from hawkentracker.views.api import api, api_response


@api.route("/ingest", methods=["POST"])
def events_ingester():
    required_fields = ["Data", "Producer", "Subject", "Target", "Timestamp", "Verb"]

    # TODO: Authenticate

    # Check we have a json payload
    payload = request.get_json()
    if not payload or not all((required_field in payload for required_field in required_fields)):
        return api_response({"error": "invalid_payload"}, status_codes.bad_request)

    # Run event handlers
    result = EventIngester.process_event(payload)

    # Return result
    if result["failed"] > 0:
        status_code = status_codes.internal_server_error
    else:
        status_code = status_codes.ok

    return api_response(result, status_code)
