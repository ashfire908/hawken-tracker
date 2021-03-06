# -*- coding: utf-8 -*-
# Hawken Tracker - Match views

from flask import Blueprint, flash, render_template

from hawkenapi.util import verify_match
from hawkentracker.interface import get_api
from hawkentracker.mappings import region_names, gametype_names, map_names
from hawkentracker.helpers import to_last, access_denied
from hawkentracker.database import Match

match = Blueprint("match", __name__, url_prefix="/match")


@match.route("/")
def list():
    return "match list"


@match.route("/<id>")
def view(id):
    api = get_api()

    # Verify the match id is valid
    if not verify_match(id):
        flash("Invalid match ID.", "error")
        return to_last()

    # Load the match's info
    match = Match.query.get(id)
    if match is None:
        flash("No match found for '{0}'.".format(id), "error")
        return to_last()

    # Build the page info
    context = {
        "match": {
            "id": match.match_id,
            "server_name": match.server_name,
            "server_region": region_names.get(match.server_region, match.server_region),
            "server_gametype": gametype_names.get(match.server_gametype, match.server_gametype),
            "server_map": map_names.get(match.server_map, match.server_map),
            "server_version": match.server_version,
            "first_seen": match.first_seen.strftime("%Y-%m-%d %H:%M"),
            "last_seen": match.last_seen.strftime("%Y-%m-%d %H:%M"),
            "mmr_avg": False,
            "pilot_level_avg": False
        }
    }

    # Stats
    context["match"].update({
        "mmr_avg": "{0:.2f}".format(match.mmr_avg),
        "pilot_level_avg": "{0:.1f}".format(match.pilot_level_avg)
    })

    # Players
    context["players"] = []

    for player in match.players:
        player = {
            "name": player.player.callsign or player.player_id,
            "first_seen": player.first_seen.strftime("%Y-%m-%d %H:%M"),
            "last_seen": player.last_seen.strftime("%Y-%m-%d %H:%M")
        }

        context["players"].append(player)

    return render_template("match/view.jade", **context)
