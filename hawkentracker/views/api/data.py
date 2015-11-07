# -*- coding: utf-8 -*-
# Hawken Tracker - Data views

from flask import request
from requests import codes as status_codes
from sqlalchemy.orm import contains_eager

from hawkentracker.interface import get_api, get_player_id
from hawkentracker.tracker import get_ranked_players, get_global_rank
from hawkentracker.mappings import ranking_fields, region_names, gametype_names, map_names
from hawkentracker.permissions import permissions_view
from hawkentracker.helpers import parse_serverside
from hawkentracker.database import Player, Match, MatchPlayer
from hawkentracker.util import value_or_default
from hawkentracker.views.api import api, api_response


@api.route("/leaderboard/global")
def global_leaderboard():
    api = get_api()

    # Validate sorts
    sort = request.args.get("sort", "mmr")
    if sort not in ranking_fields:
        sort = "mmr"
    additional = [extra for extra in request.args.get("extra", "").split(",") if extra in ranking_fields and extra != sort]

    # Load the data
    players = get_ranked_players(sort, 100, preload=additional)
    rankings = get_global_rank([player.player_id for player in players], sort)[0]

    # Format it for return
    items = []
    for player in players:
        item = {}

        # Add rank
        item["rank"] = rankings[player.player_id]

        # Add player info
        if permissions_view.player.player(player.player_id).leaderboard:
            item["player"] = player.callsign or player.player_id
            item["first_seen"] = player.first_seen.strftime("%Y-%m-%d %H:%M")
            item["last_seen"] = player.last_seen.strftime("%Y-%m-%d %H:%M")
            if permissions_view.player.player(player.player_id).region:
                region = (player.home_region or player.common_region)
                item["region"] = region_names.get(region, region)
            else:
                item["region"] = None
        else:
            item["player"] = None
            item["first_seen"] = None
            item["last_seen"] = None
            item["region"] = None

        if permissions_view.player.player(player.player_id).stats.ranked:
            for stat in additional:
                if sort != stat:
                    item[stat] = getattr(player.stats, stat)
            item[sort] = getattr(player.stats, sort)

        items.append(item)

    # Return it
    return api_response({"data": items}, status_codes.ok)


@api.route("/player/<player>/matches", methods=["POST"])
def player_matches(player):
    # Get the target player
    guid, _ = get_player_id(player, False)
    if guid is None:
        # No such player
        return api_response({"error": "No such player"}, status_codes.not_found)

    # Load the player
    player = Player.query.get(guid)

    if player is None:
        # No such player tracked
        return api_response({"error": "No tracked player"}, status_codes.not_found)

    if not permissions_view.player.player(player.player_id).match.list:
        # Player's matches are private
        return api_response({"error": "Player matches are private"}, status_codes.forbidden)

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

    for match in matches:
        data["recordsTotal"] += 1

        if not permissions_view.player.player(player.player_id).match.match(match.match_id).view:
            continue

        # Add match info
        item = {
            "id": match.match_id,
            "server_name": match.match.server_name,
            "server_region": value_or_default(region_names.get(match.match.server_region, None), match.match.server_region),
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

    # Return it
    return api_response(data, status_codes.ok)
