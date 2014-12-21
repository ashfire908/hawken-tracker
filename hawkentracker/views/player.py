# -*- coding: utf-8 -*-
# Hawken Tracker - PLayer views

import math
from collections import OrderedDict

from flask import Blueprint, flash, render_template, current_app
from hawkentracker.interface import get_api, get_player_id
from hawkentracker.mappings import region_names, ranking_fields, ranking_names_full, LinkStatus
from hawkentracker.permissions import permissions_view
from hawkentracker.helpers import to_last, access_denied, format_stat
from hawkentracker.model import Player
from hawkentracker.tracker import get_global_rank

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

    # Access check
    if not permissions_view.player.player(player.id).view:
        if player.opt_out:
            flash("This player has opted out of the leaderboards and their profile is private.", "info")
            return to_last()
        return access_denied("You do not have permission to view this player.")

    # Build the page info
    context = {
        "info": {
            "name": callsign or guid,
            "first_seen": player.first_seen,
            "last_seen": player.last_seen,
            "home_region": False,
            "common_region": False,
            "blacklisted": player.blacklisted,
            "blacklist_reason": None
        },
        "edit": {
            "settings": permissions_view.player.player(player.id).settings,
            "blacklist": permissions_view.player.blacklist.change
        },
        "ranking": False,
        "stats": False,
        "mechs": False,
        "matches": permissions_view.player.player(player.id).match.list,
        "groups": False
    }

    # Blacklist
    if player.blacklisted and permissions_view.player.blacklist.view:
        context["info"]["blacklist_reason"] = player.blacklist_reason

    # Region
    if permissions_view.player.player(player.id).region:
        context["info"].update({
            "home_region": player.home_region,
            "common_region": player.common_region
        })

    # Rankings
    if permissions_view.player.player(player.id).rankings:
        if player.stats is None:
            context["ranking"] = None
        else:
            # Ranked stats
            show_stats = permissions_view.player.player(player.id).stats.ranked
            context["ranking"] = OrderedDict()
            for field in ranking_fields:
                stat = getattr(player.stats, field, None)
                if stat is None:
                    continue
                rank, total = get_global_rank(player.id, field)
                percentage = rank / total
                context["ranking"][ranking_names_full[field]] = (format_stat(stat, field) if show_stats else False, "Rank #%i" % rank if percentage < current_app.config["RANK_PERCENT_THRESHOLD"] else "Top {0:.0f}%".format(math.ceil(percentage * 100)))

    # Global stats
    if permissions_view.player.player(player.id).stats.overall:
        context["stats"] = {}

    # Mech stats
    if permissions_view.player.player(player.id).stats.mech:
        context["mechs"] = []

    # Groups
    if permissions_view.player.player(player.id).group:
        context["groups"] = []

    # Linked players
    context["linked"] = {
        "status": player.link_status == LinkStatus.linked,
        "user": None,
        "players": None
    }
    if context["linked"]["status"]:
        if permissions_view.player.player(player.id).link.user:
            context["linked"]["user"] = {
                "id": player.user.id,
                "name": player.user.username
            }

        if permissions_view.player.player(player.id).link.players:
            players = Player.query.filter(Player.link_user == player.user.id).filter(Player.link_status == LinkStatus.linked).filter(Player.id != guid)
            context["linked"]["players"] = [api.get_user_callsign(player.id) or player.id for player in players]

    return render_template("player/view.jade", **context)


@player.route("/<target>/settings", methods=["GET", "POST"])
def settings(target):
    # Get the target player
    guid, callsign = get_player_id(target)
    if guid is None:
        flash("No such player exists.", "error")
        return to_last()

    # Load the player's info
    player = Player.query.get(guid)
    if player is None:
        flash("'{0}' has not been tracked by the system yet. Please try playing a match first for at least a minute and then initiate a link from ScrimBot.".format(callsign or guid), "error")
        return to_last()

    # Access check
    if not permissions_view.player.player(player.id).settings:
        return access_denied("You do not have permission to edit this player's settings.")

    # Build the page info
    context = {
        "name": callsign or guid,
        "player": player,
        "regions": region_names
    }

    return render_template("player/settings.jade", **context)
