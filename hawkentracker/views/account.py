# -*- coding: utf-8 -*-
# Hawken Tracker - Account views

from flask import Blueprint, render_template, request, flash, session
from hawkentracker.account import get_user, set_password, ValidationError, load_password_reset_token, link_player, unlink_player, \
    load_email_verify_token, confirm_email, delete_user, logout_user
from hawkentracker.helpers import to_next, to_last, login_required, access_denied, load_globals
from hawkentracker.interface import get_api, get_player_id
from hawkentracker.mappings import LinkStatus
from hawkentracker.model import Player
from hawkentracker.permissions import permissions_view

account = Blueprint("account", __name__, url_prefix="/account")


@account.route("/")
@login_required
def overview():
    # Get the user's account
    user = get_user()

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
    return render_template("account/overview.jade", LinkStatus=LinkStatus, **context)


@account.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    # Get the user's account
    user = get_user()

    # Access check
    if not permissions_view.user.user(user.id).settings:
        return access_denied("You do not have permission to edit this user's settings.")


    return "account settings"
    if request.method == "POST":
        # Check settings
        #flash("Settings successfully saved!", "success")
        pass


    load_globals()
    return render_template("account/settings.jade", **context)


@account.route("/password", methods=["GET", "POST"])
@login_required
def password():
    # Get the user's account
    user = get_user()

    # Access check
    if not permissions_view.user.user(user.id).password:
        return access_denied("You do not have permission to edit this user's password.")

    if request.method == "POST":
        # Check fields
        if request.args["new_password"] != request.args["confirm_password"]:
            flash("The new passwords must match.", "error")
        elif user.verify_password(request.args["current_password"]):
            flash("The current password does not match the password on file.", "error")
        else:
            try:
                set_password(user.id, request.form["password"])
            except ValidationError as e:
                flash(str(e), "error")
            else:
                flash("Password successfully changed!", "error")
                return to_next("login")


    return "change password"


@account.route("/password/reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    try:
        user = load_password_reset_token(token)
    except ValidationError as e:
        flash("Invalid token: {0}".format(e), "error")
        return to_last()

    if request.method == "POST":
        if request.form["password"] != request.form["confirm"]:
            flash("The passwords must match.", "error")
        else:
            try:
                set_password(user, request.form["password"])
            except ValidationError as e:
                flash(str(e), "error")
            else:
                flash("Password successfully reset!", "error")
                return to_next("login")

    load_globals()
    return render_template("account/password_reset.jade")


@account.route("/link/<target>")
@login_required
def link_player(target):
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

    # Get the user's account
    user = get_user()

    # Access check
    if not permissions_view.user.user(user.id).link.player(guid).add:
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
    link_player(user.id, player)

    flash("'{0}' has successfully been linked to your account".format(callsign or guid), "success")
    return to_next("account")


@account.route("/unlink/<target>")
@login_required
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
    user = get_user()

    # Access check
    if not permissions_view.user.user(user.id).link.player(guid).remove:
        if player.link_user != user.id or player.link_status == LinkStatus.none:
            flash("No link is established or pending between this user and your account.", "error")
        else:
            return access_denied("You do not have permission to unlink to this player.")

        return to_last()

    # Link the player
    unlink_player(player)

    flash("'{0}' has been successfully unlinked from your account".format(callsign), "success")
    return to_next("account")


@account.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    # Get the user's account
    user = get_user()

    # Access check
    if not permissions_view.user.user(user.id).delete:
        return access_denied("You do not have permission to delete this user.")

    if request.method == "POST":
        if request.form["username"] != user.username:
            flash("Invalid delete confirmation.", "error")
        else:
            # Logout and delete the user
            logout_user()
            delete_user(user.id)
            flash("User successfully deleted!", "success")

            return to_next()

    load_globals()
    return render_template("account/delete.jade")


@account.route("/verify/<token>")
def verify_email(token):
    try:
        user = load_email_verify_token(token)
    except ValidationError as e:
        flash("Invalid token: {0}".format(e), "error")
        return to_last()

    # Confirm email
    confirm_email(user)

    flash("Email successfully verified!", "success")

    if session.get("user", None) == user.id:
        return to_next("account")

    return to_next("login")
