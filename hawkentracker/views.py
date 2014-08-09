# -*- coding: utf-8 -*-
# Hawken Tracker - Views

from collections import OrderedDict
from sqlalchemy import func
from sqlalchemy.orm import contains_eager
from flask import render_template, request, session, flash, jsonify, abort
from hawkenapi.util import verify_match
from hawkentracker import app
from hawkentracker.account import ValidationError, get_user, login_user, logout_user, create_user, link_player, unlink_player, \
    load_email_verify_token, confirm_email, load_password_reset_token, set_password, delete_user, verify_password, \
    send_password_reset_email, send_reminder_email
from hawkentracker.helpers import login_required, access_denied, to_next, to_last, format_stat, parse_serverside, load_globals
from hawkentracker.interface import get_api, get_player_id
from hawkentracker.mappings import CoreRole, LinkStatus, ranking_fields, ranking_names, region_names, gametype_names, map_names, ranking_names_full
from hawkentracker.model import Player, Match, MatchPlayer, dump_queries, User
from hawkentracker.tracker import get_ranked_players, get_global_rank
from hawkentracker.util import value_or_default
from hawkentracker.permissions import permissions_view


@app.route("/")
def index():
    context = {
        "sort_fields": ranking_fields,
        "sort_names": ranking_names,
        "default_sort": "mmr"
    }

    load_globals()
    return render_template("leaderboard/leaderboard.jade", **context)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in", False):
        flash("You are already logged in.", "info")
        return to_next("account")

    if request.method == "POST":
        if not login_user(request.form["username"], request.form["password"]):
            flash("Invalid login.", "error")
        else:
            flash("Successfully logged in!", "success")
            return to_next()

    load_globals()
    return render_template("account/login.jade")


@app.route("/login/forgot", methods=["GET", "POST"])
def forgot_login():
    if session.get("logged_in", False):
        flash("You are already logged in.", "info")
        return to_next("account")

    if request.method == "POST":
        if request.form["username"] != "":
            user = User.query.filter(func.lower(User.username) == request.form["username"].lower()).first()
            if user is not None:
                send_password_reset_email(user)

            flash("Password reset email sent.", "success")
            return to_next("login")

        if request.form["email"] != "":
            user = User.query.filter(func.lower(User.email) == request.form["email"].lower()).first()
            if user is not None:
                send_reminder_email(user)
                flash("A reminder email with your account details has been sent.", "success")
                return to_next("login")

            flash("No user was found with that email.", "error")
        else:
            flash("Please specify either your username or email.", "error")

    load_globals()
    return render_template("account/forgot.jade")


@app.route("/logout")
def logout():
    if logout_user():
        flash("You have been logged out.", "success")

    return to_next()


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("logged_in", False):
        flash("You are already logged in.", "info")
        return to_next("account")
    elif permissions_view.user.create.self:
        return access_denied("You do not have permission to create a user.")

    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()

        if request.form["password"] != request.form["confirm"]:
            flash("The passwords must match.", "error")
        else:
            try:
                create_user(username, request.form["password"], email, CoreRole.unconfirmed.value)
                flash("Successfully registered!", "success")
                if not login_user(username, request.form["password"]):
                    app.logger.error("Failed to automatically login user '{0}' with their own password".format(username))
                    flash("Failed to log you in. Please contact the administrator.", "error")
                else:
                    return to_next("account")
            except ValidationError as e:
                flash(str(e), "error")

    load_globals()
    return render_template("account/register.jade")

@app.route("/account")
@login_required
def account():
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
    return render_template("account/account.jade", LinkStatus=LinkStatus, **context)


@app.route("/account/settings", methods=["GET", "POST"])
@login_required
def account_settings():
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


@app.route("/account/password", methods=["GET", "POST"])
@login_required
def account_password():
    # Get the user's account
    user = get_user()

    # Access check
    if not permissions_view.user.user(user.id).password:
        return access_denied("You do not have permission to edit this user's password.")

    if request.method == "POST":
        # Check fields
        if request.args["new_password"] != request.args["confirm_password"]:
            flash("The new passwords must match.", "error")
        elif not verify_password(user, request.args["current_password"]):
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


@app.route("/account/password-reset/<token>", methods=["GET", "POST"])
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


@app.route("/account/link/<target>")
@login_required
def account_link_player(target):
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


@app.route("/account/unlink/<target>")
@login_required
def account_unlink_player(target):
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


@app.route("/account/delete", methods=["GET", "POST"])
@login_required
def delete_account():
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
            logout()
            delete_user(user.id)
            flash("User successfully deleted!", "success")

            return to_next()

    load_globals()
    return render_template("account/delete.jade")


@app.route("/account/verify/<token>")
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


@app.route("/user/<user>")
def view_user(user):
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
    return render_template("account/profile.jade", LinkStatus=LinkStatus, **context)


@app.route("/player/<target>")
def view_player(target):
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
                context["ranking"][ranking_names_full[field]] = (format_stat(stat, field) if show_stats else False, get_global_rank(player.id, field))

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

    dump_queries("view_player")
    load_globals()
    return render_template("player/player.jade", **context)


@app.route("/player/<target>/settings", methods=["GET", "POST"])
def player_settings(target):
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


@app.route("/match")
def match_list():
    return "match list"


@app.route("/match/<id>")
def match(id):
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

    # Access check
    if not permissions_view.match.match(match.id).view:
        return access_denied("You do not have permission to view this match.")

    # Build the page info
    context = {
        "match": {
            "id": match.id,
            "server_name": match.server_name,
            "server_region": region_names.get(match.server_region, match.server_region),
            "server_gametype": gametype_names.get(match.server_gametype, match.server_gametype),
            "server_map": map_names.get(match.server_map, match.server_map),
            "server_version": match.server_version,
            "first_seen": match.first_seen.strftime("%Y-%m-%d %H:%M"),
            "last_seen": match.last_seen.strftime("%Y-%m-%d %H:%M"),
            "average_mmr": False,
            "average_level": False
        }
    }

    # Stats
    if permissions_view.match.match(match.id).stats:
        context["match"].update({
            "average_mmr": match.average_mmr,
            "average_level": match.average_level
        })

    # Players
    if permissions_view.match.match(match.id).players:
        context["players"] = []

        for player in match.players:
            if permissions_view.player.player(player.player_id).match:
                player = {
                    "name": api.get_user_callsign(player.player_id) or player.player_id,
                    "first_seen": player.first_seen.strftime("%Y-%m-%d %H:%M"),
                    "last_seen": player.last_seen.strftime("%Y-%m-%d %H:%M")
                }
            else:
                player = {
                    "name": None,
                    "first_seen": None,
                    "last_seen": None
                }

            context["players"].append(player)

    load_globals()
    return render_template("match/match.jade", **context)


#@app.route("/group")
#def list_groups():
#    return "group list"
#
#
#@app.route("/group/<id>")
#def group(id):
#    return "group"
#
#
#@app.route("/group/<id>/roster")
#def group_roster(id):
#    return "group roster"
#
#
#@app.route("/group/<id>/join", methods=["POST"])
#@login_required
#def join_group(id):
#    return "join group"
#
#
#@app.route("/group/<id>/leave", methods=["POST"])
#@login_required
#def leave_group(id):
#    return "leave group"
#
#
#@app.route("/group/<id>/preferences", methods=["GET", "POST"])
#@login_required
#def group_preferences(id):
#    return "group preferences"
#
#
#@app.route("/group/<id>/create", methods=["GET", "POST"])
#@login_required
#def create_group():
#    return "create group"
#
#
#@app.route("/group/<id>/edit", methods=["POST"])
#@login_required
#def edit_group(id):
#    return "edit group"
#
#
#@app.route("/group/<id>/delete", methods=["GET", "POST"])
#@login_required
#def delete_group(id):
#    return "delete group"
#
#
#@app.route("/group/<id>/dashboard")
#@login_required
#def group_dashboard(id):
#    return "group dashboard"
#
#
#@app.route("/group/<id>/member/edit", methods=["POST"])
#@login_required
#def edit_member(id):
#    return "edit member"
#
#
#@app.route("/group/<id>/member/invite", methods=["POST"])
#@login_required
#def invite_member(id):
#    return "invite member"
#
#
#@app.route("/group/<id>/member/remove", methods=["POST"])
#@login_required
#def remove_member(id):
#    return "remove member"


@app.route("/data/leaderboard/global")
def global_leaderboard():
    api = get_api()

    # Validate sorts
    sort = request.args.get("sort", "mmr")
    if sort not in ranking_fields:
        sort = "mmr"
    additional = [extra for extra in request.args.get("extra", "").split(",") if extra in ranking_fields and extra != sort]

    # Load the data
    players = get_ranked_players(sort, 100, preload=additional)
    rankings = get_global_rank([player.id for player in players], sort)

    # Format it for return
    items = []
    for player in players:
        item = {}

        # Add rank
        item["rank"] = rankings[player.id]

        # Add player info
        if permissions_view.player.player(player.id).leaderboard:
            item["player"] = api.get_user_callsign(player.id) or player.id
            item["first_seen"] = player.first_seen.strftime("%Y-%m-%d %H:%M")
            item["last_seen"] = player.last_seen.strftime("%Y-%m-%d %H:%M")
            if permissions_view.player.player(player.id).region:
                region = (player.home_region or player.common_region)
                item["region"] = region_names.get(region, region)
            else:
                item["region"] = None
        else:
            item["player"] = None
            item["first_seen"] = None
            item["last_seen"] = None
            item["region"] = None

        if permissions_view.player.player(player.id).stats.ranked:
            for stat in additional:
                if sort != stat:
                    item[stat] = getattr(player.stats, stat)
            item[sort] = getattr(player.stats, sort)

        items.append(item)

    # Return it
    return jsonify(data=items)


@app.route("/data/player/<player>/matches", methods=["POST"])
def player_matches(player):
    api = get_api()

    # Get the target player
    guid, _ = get_player_id(player, False)
    if guid is None:
        # No such player
        abort(404)

    # Load the player
    player = Player.query.get(guid)

    if player is None:
        # No such player tracked
        abort(404)

    if not permissions_view.player.player(player.id).match.list:
        # Player's matches are private
        abort(401)

    # Parse the request info
    request_info = parse_serverside(request.form)
    draw = request_info.get("draw", None)
    start = int(request_info.get("start", 0))
    length = min((int(request_info.get("length", 50)), 100))
    end = start + length
    columns = {column["data"]: column for column in request_info.get("columns", {}).values()}
    try:
        order = request_info["columns"][request_info["order"]["0"]["column"]]["data"]
        if order not in ("id", "server_name", "server_region", "server_gametype", "server_map", "server_version", "first_seen", "last_seen"):
            order = "last_seen"
        direction = request_info["order"]["0"]["dir"]
        if direction not in ("asc", "desc"):
            direction = "desc"
    except KeyError:
        order = "last_seen"
        direction = "desc"

    # Load the matches and return the data
    data = {
        "recordsTotal": 0,
        "recordsFiltered": 0,
        "data": []
    }

    if draw is not None:
        data["draw"] = int(draw)

    # Determine the sort
    if order in ("id", "server_name", "server_region", "server_gametype", "server_map", "server_version"):
        sort = getattr(getattr(Match, order), direction)()
    else:
        sort = getattr(getattr(MatchPlayer, order), direction)()

    matches = MatchPlayer.query.join(MatchPlayer.match).filter(MatchPlayer.player_id == guid).options(contains_eager(MatchPlayer.match)).order_by(sort).all()

    show_all = permissions_view.player.player(player.id).match.view
    #ids = [match.id for match in matches]
    #view_perm = {id: perm for id, perm in zip(ids, permissions_view.match.match(ids).view)}

    for match in matches:
        data["recordsTotal"] += 1

        #if not view_perm[match.match_id]:
        if not show_all and not permissions_view.match.match(match.match_id).view:
            continue

        # Add match info
        item = {
            "id": match.match_id,
            "server_name": match.match.server_name,
            "server_region": value_or_default(region_names[match.match.server_region], match.match.server_region),
            "server_gametype": value_or_default(gametype_names[match.match.server_gametype], match.match.server_gametype),
            "server_map": value_or_default(map_names[match.match.server_map], match.match.server_map),
            "server_version": match.match.server_version,
            "first_seen": match.first_seen.strftime("%Y-%m-%d %H:%M"),
            "last_seen": match.last_seen.strftime("%Y-%m-%d %H:%M")
        }

        # Check we have something to search against
        search = request_info["search"]["value"].lower()
        if search != "":
            if item["id"] is not None:
                # Apply search filter
                for col, val in columns.items():
                    # Check that this column is searchable and we found a match
                    if val["searchable"] == "true" and item[col].lower().find(search) >= 0:
                        if start <= data["recordsFiltered"] <= end:
                            data["data"].append(item)
                        data["recordsFiltered"] += 1
                        break
        else:
            # No active search, add to the data
            if start <= data["recordsFiltered"] <= end:
                data["data"].append(item)
            data["recordsFiltered"] += 1

    dump_queries("player_matches")

    # Return it
    return jsonify(**data)
