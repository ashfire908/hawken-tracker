# -*- coding: utf-8 -*-
# Hawken Tracker - Account views

from flask import Blueprint, render_template, request, flash
from flask.ext.login import login_required, fresh_login_required, current_user
from hawkentracker.account import delete_user, logout_user
from hawkentracker.helpers import to_next, to_last, access_denied
from hawkentracker.interface import get_api, get_player_id
from hawkentracker.mappings import LinkStatus
from hawkentracker.models.database import Player, db
from hawkentracker.permissions import permissions_view

account = Blueprint("account", __name__, url_prefix="/account")


@account.route("/")
@login_required
def overview():
    # Access check
    if not permissions_view.user.user(current_user.id).view:
        return access_denied("You do not have permission to view this user.")

    # Get the Hawken API
    api = get_api()

    # Build the page info
    context = {
        "user": current_user,
        "players": False,
        "delete": permissions_view.user.user(current_user.id).delete,
        "settings": permissions_view.user.user(current_user.id).settings,
        "password": permissions_view.user.user(current_user.id).password
    }

    if permissions_view.user.user(current_user.id).link.list:
        context["players"] = {api.get_user_callsign(player.id) or player.id: player for player in current_user.players if player.link_status != LinkStatus.none}

    return render_template("account/overview.jade", LinkStatus=LinkStatus, **context)


@account.route("/settings", methods=["GET", "POST"])
@fresh_login_required
def settings():
    # Access check
    if not permissions_view.user.user(current_user.id).settings:
        return access_denied("You do not have permission to edit this user's settings.")

    if request.method == "POST":
        flash("Not implemented yet.", "error")

    return render_template("account/settings.jade")


@account.route("/password", methods=["GET", "POST"])
@fresh_login_required
def password():
    # Access check
    if not permissions_view.user.user(current_user.id).password:
        return access_denied("You do not have permission to edit this user's password.")

    if request.method == "POST":
        user = current_user

        # Check fields
        if request.args["new_password"] != request.args["new_password_confirm"]:
            flash("The new passwords must match.", "error")
        elif user.verify_password(request.args["password"]):
            flash("The current password does not match the password on file.", "error")
        else:
            user.set_password(request.form["password"])

            db.session.add(user)
            db.session.commit()

            flash("Password successfully changed!", "error")
            return to_next("account.overview")

    return render_template("account/password.jade")


@account.route("/link/<target>")
@fresh_login_required
def link_player(target):
    # Get the target player
    guid, callsign = get_player_id(target)
    if guid is None:
        flash("No such player exists.", "error")
        return to_last()

    # Load the player's info
    player = Player.query.get(guid)
    if player is None:
        flash("'{0}' has not been tracked by the system yet. Please initiate a link from ScrimBot.".format(callsign or guid), "error")
        return to_last()

    # Get the user's account
    user = current_user

    # Access check
    if not permissions_view.user.user(user.id).link.player(player.id).add:
        if player.link_user == user.id and player.link_status == LinkStatus.linked:
            flash("You are already linked to this player.", "error")
        elif player.link_status == LinkStatus.none:
            flash("No link is pending from this player. Please initiate a link from ScrimBot.", "error")
        elif player.link_user != user.id:
            flash("This player is linked to another user already.", "error")
        else:
            return access_denied("You do not have permission to link to this player.")

        return to_last()

    # Link the player
    player.link()

    db.session.add(player)
    db.session.commit()

    flash("'{0}' has successfully been linked to your account".format(callsign or guid), "success")
    return to_next("account.overview")


@account.route("/unlink/<target>")
@fresh_login_required
def unlink_player(target):
    # Get the target player
    guid, callsign = get_player_id(target)
    if guid is None:
        flash("No such player exists.", "error")
        return to_last()

    # Load the player's info
    player = Player.query.get(guid)
    if player is None:
        flash("'{0}' has not been tracked by the system yet.".format(callsign or guid), "error")
        return to_last()

    # Get the user's account
    user = current_user

    # Access check
    if not permissions_view.user.user(user.id).link.player(player.id).remove:
        if player.link_user != user.id or player.link_status == LinkStatus.none:
            flash("No link is established or pending between this user and your account.", "error")
        else:
            return access_denied("You do not have permission to unlink to this player.")

        return to_last()

    # Link the player
    player.unlink()

    db.session.add(player)
    db.session.commit()

    flash("'{0}' has been successfully unlinked from your account".format(callsign or guid), "success")
    return to_next("account.overview")


@account.route("/delete", methods=["GET", "POST"])
@fresh_login_required
def delete():
    # Access check
    if not permissions_view.user.user(current_user.id).delete:
        return access_denied("You do not have permission to delete this user.")

    if request.method == "POST":
        if request.form["username"] != current_user.username:
            flash("Invalid delete confirmation.", "error")
        else:
            # Get the user's account
            user = current_user

            # Logout and delete the user
            logout_user()
            delete_user(user)
            flash("User successfully deleted!", "success")

            return to_next()

    return render_template("account/delete.jade")
