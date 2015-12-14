# -*- coding: utf-8 -*-
# Hawken Tracker - Player views

import math
from collections import OrderedDict

from flask import Blueprint, flash, render_template, current_app

from hawkentracker.interface import get_api, get_player_id
from hawkentracker.mappings import ranking_fields, ranking_names_full
from hawkentracker.helpers import to_last, format_stat
from hawkentracker.database import Player

player = Blueprint("player", __name__, url_prefix="/player")


@player.route("/<target>")
def view(target):
    api = get_api()

    # Get the target player
    guid, callsign = get_player_id(target)
    if guid is None:
        flash("No such player exists.", "error")
        return to_last()

    # Load the player's info
    player = Player.query.get(guid)
    if player is None:
        flash("'{0}' has not been tracked by the system yet. If this is your account, please try playing a match first for at least a minute.".format(callsign or guid), "error")
        return to_last()

    # Build the page info
    context = {
        "info": {
            "name": callsign or guid,
            "first_seen": player.first_seen,
            "last_seen": player.last_seen,
            "common_region": False,
            "blacklisted": player.blacklisted,
            "blacklist_reason": None
        },
        "edit": {
            "settings": False,
            "blacklist": False
        },
        "ranking": False,
        "stats": False,
        "mechs": False,
        "matches": False,
        "groups": False
    }

    # Blacklist
    if player.blacklisted:
        context["info"]["blacklist_reason"] = player.blacklist_reason

    # Region
    context["info"].update({
        "common_region": player.common_region
    })

    # Rankings
    if player.stats is None:
        context["ranking"] = None
    else:
        # Ranked stats
        context["ranking"] = OrderedDict()
        for field in ranking_fields:
            stat = getattr(player.stats, field, None)
            if stat is None:
                continue
            rank = getattr(player.rankings, field)
            total = getattr(player.rankings.snapshot, field)
            if rank is None:
                context["ranking"][ranking_names_full[field]] = (format_stat(stat, field), "Unranked")
            else:
                percentage = rank / total
                context["ranking"][ranking_names_full[field]] = (format_stat(stat, field), "Rank #%i" % rank if percentage < current_app.config["RANK_PERCENT_THRESHOLD"] else "Top {0:.0f}%".format(math.ceil(percentage * 100)))

    # Global stats
    context["stats"] = {}

    # Mech stats
    context["mechs"] = []

    # Groups
    context["groups"] = []

    return render_template("player/view.jade", **context)
