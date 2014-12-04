# -*- coding: utf-8 -*-
# Hawken Tracker - PLayer views

from flask import Blueprint, render_template
from hawkentracker.interface import get_api
from hawkentracker.mappings import LinkStatus
from hawkentracker.permissions import permissions_view
from hawkentracker.helpers import access_denied, load_globals

user = Blueprint("user", __name__, url_prefix="/user")


@user.route("/<user>")
def view(user):
    # Get the user's account
    user = get_user_by_name(user)

    # Access check
    if not permissions_view.user.user(user.id).view:
        return access_denied("You do not have permission to view this user.")

    # Get the Hawken API
    api = get_api()

    # Build the page info
    context = {
        "user": user,
        "players": False,
        "delete": permissions_view.user.user(user.id).delete,
        "settings": permissions_view.user.user(user.id).settings,
        "password": permissions_view.user.user(user.id).password
    }

    if permissions_view.user.user(user.id).link.list:
        context["players"] = {api.get_user_callsign(player.id) or player.id: player for player in user.players if player.link_status != LinkStatus.none}

    load_globals()
    return render_template("user/view.jade", LinkStatus=LinkStatus, **context)
