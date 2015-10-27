# -*- coding: utf-8 -*-
# Hawken Tracker - User views

from flask import Blueprint, render_template

from hawkentracker.helpers import access_denied
from hawkentracker.interface import get_api
from hawkentracker.mappings import LinkStatus
from hawkentracker.database import User
from hawkentracker.permissions import permissions_view

user = Blueprint("user", __name__, url_prefix="/user")


@user.route("/<username>")
def view(username):
    # Get the user's account
    user = User.by_username(username)

    # Access check
    if not permissions_view.user.user(user.user_id).view:
        return access_denied("You do not have permission to view this user.")

    # Get the Hawken API
    api = get_api()

    # Build the page info
    context = {
        "user": user,
        "players": False,
        "delete": permissions_view.user.user(user.user_id).delete,
        "settings": permissions_view.user.user(user.user_id).settings,
        "password": permissions_view.user.user(user.user_id).password
    }

    if permissions_view.user.user(user.user_id).link.list:
        context["players"] = {player.callsign or player.player_id: player for player in user.players if player.link_status != LinkStatus.none}

    return render_template("user/view.jade", LinkStatus=LinkStatus, **context)
