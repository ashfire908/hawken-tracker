# -*- coding: utf-8 -*-
# Hawken Tracker - Permissions

import types
import logging
from flask import g
from hawkenapi.util import copyappend
from hawkentracker import app
from hawkentracker.account import get_user
from hawkentracker.mappings import LinkStatus, CoreRole, default_privacy
from hawkentracker.model import Player, Match, UserRole, db

logger = logging.getLogger(__name__)


# Permission view
def param_wrapper(map):
    if not isinstance(map, (dict, types.FunctionType, types.MethodType)):
        raise ValueError("Expected dict map, function, or method")

    def lookup_wrapper(path):
        def lookup_argument(argument):
            path.append(argument)
            if isinstance(map, dict):
                return PermissionView(map, path=path)
            else:
                return map(path)

        return lookup_argument

    lookup_wrapper._lookup_wrapper = True
    return lookup_wrapper


class PermissionView:
    def __init__(self, map, path=None):
        if not isinstance(map, dict):
            raise TypeError("Expected dict")
        if path is None:
            path = []
        self.map = map
        self.path = path

    def __getitem__(self, key):
        target = self.map[key]
        if hasattr(target, "_lookup_wrapper"):
            return target(self.path)
        else:
            path = copyappend(self.path, key)
            if isinstance(target, (types.FunctionType, types.MethodType)):
                return target(path)

            return PermissionView(target, path=path)

    def __bool__(self):
        if "_" in self.map and callable(self.map["_"]):
            # noinspection PyCallingNonCallable
            return self.map["_"](self.path)

        raise ValueError("This permission view cannot be used directly")

    __getattr__ = __getitem__


# Helpers
def get_current_user():
    user = g.get("user", None)
    if user is None:
        # Lookup and set user
        user = get_user()
        if user is None:
            user = False
        g.user = user

    return user


def get_permission(permission, names=None):
    user_permissions = g.get("user_permissions", None)
    if user_permissions is None:
        # Build permissions list
        user = get_current_user()
        if user is False:
            user_role = UserRole.query.get(CoreRole.anonymous.value)
        else:
            user_role = user.role

        if user_role.superadmin:
            user_permissions = True
        else:
            user_permissions = {}
            for user_perm in user_role.permissions:
                user_permissions[user_perm.permission] = user_perm.power if user_perm.power is not None else True

        g.user_permissions = user_permissions

    # Check for superadmin
    if user_permissions is True:
        return True, None

    if isinstance(permission, (list, tuple)):
        # Rebuild the permission string
        if names is None:
            permission = ".".join(permission)
        else:
            first = True
            path = ""
            for x, name in zip(permission, names):
                if first:
                    first = False
                else:
                    path += "."

                path += name or x

            permission = path

    return user_permissions.get(permission, 0), default_privacy.get(permission, None)


def satifies_perm(permission, power, default):
    if permission is True:
        return True

    if power is None:
        if default is None:
            raise ValueError("Default privacy power not set but being compared")
        privacy = default
    else:
        privacy = power

    return privacy <= permission


def user_linked_players(user):
    if user:
        return [player.id for player in user.players if player.link_status == LinkStatus.linked]
    return []


# Permission handlers
def basic_flag(path):
    return get_permission(path)[0]


def user_view(path):
    perm, default = get_permission(path, names=(None, "user", None))
    if perm is True:
        # Global permission given
        return True

    user = get_current_user()

    if user and path[1] == user.id:
        # User is viewing themselves
        return True

    if satifies_perm(perm, get_user(path[1]).view_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def user_delete(path):
    perm, default = get_permission(path, names=(None, "user", None))
    if perm is True:
        # Global permission given
        return True

    user = get_current_user()

    if user and path[1] == user.id:
        # User is deleting themselves
        return True


def user_settings(path):
    perm, default = get_permission(path, names=(None, "user", None))
    if perm is True:
        # Global permission given
        return True

    user = get_current_user()

    if user and path[1] == user.id:
        # User is editing their own settings
        return True

    return False


def user_role(path):
    perm, default = get_permission(path, names=(None, "user", None))
    if perm is not True:
        # Global permission not given
        return False

    user = get_current_user()

    if user and path[1] == user.id:
        # User is editing their own role
        return False

    return True


def user_password(path):
    perm, default = get_permission(path, names=(None, "user", None))
    if perm is True:
        # Global permission given
        return True

    user = get_current_user()

    if user and path[1] == user.id:
        # User is changing their own password
        return True

    return False


def user_link_list(path):
    perm, default = get_permission(path, names=(None, "user", None, None))
    if perm is True:
        # Global permission given
        return True

    user = get_current_user()

    if user and path[1] == user.id:
        # User is listing their own linked players
        return True

    if satifies_perm(perm, get_user(path[1]).link_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def user_link_add(path):
    perm, default = get_permission(path, names=(None, "user", None, "player", None))
    if perm is True:
        # Global permission given
        return True

    user = get_current_user()

    if user and path[1] == user.id:
        # User matches requested user
        player = Player.query.get(path[3])

        if player.link_user == user.id and player.link_status == LinkStatus.pending:
            # User is linking against a pending linked player
            return True

    return False


def user_link_remove(path):
    perm, default = get_permission(path, names=(None, "user", None, "player", None))
    if perm is True:
        # Global permission given
        return True

    user = get_current_user()

    if user and path[1] == user.id:
        # User matches requested user
        player = Player.query.get(path[3])

        if player.link_user == user.id and player.link_status in (LinkStatus.pending, LinkStatus.linked):
            # User is unlinking a pending or linked player
            return True

    return False


def player_view(path):
    perm, default = get_permission(path, names=(None, "player", None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.view_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_region(path):
    perm, default = get_permission(path, names=(None, "player", None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.region_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_leaderboard(path):
    perm, default = get_permission(path, names=(None, "player", None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.leaderboard_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_rankings(path):
    perm, default = get_permission(path, names=(None, "player", None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.leaderboard_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_stats_ranked(path):
    perm, default = get_permission(path, names=(None, "player", None, None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.ranked_stats_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_stats_overall(path):
    perm, default = get_permission(path, names=(None, "player", None, None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.overall_stats_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_stats_mech(path):
    perm, default = get_permission(path, names=(None, "player", None, None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.mech_stats_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_match_list(path):
    perm, default = get_permission(path, names=(None, "player", None, None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.match_list_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_match_view(path):
    perm, default = get_permission(path, names=(None, "player", None, "match", None))
    user = get_current_user()
    linked_players = user_linked_players(user)

    if user and path[1] in linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.match_view_privacy, default):
        # User meets the privacy requirement
        return True

    match = Match.query.get(path[3])

    for player in match.players:
        if player.player_id in linked_players:
            # User has played in the match
            return True

    return False


def player_group(path):
    perm, default = get_permission(path, names=(None, "player", None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.group_privacy, default):
        # User meets the privacy requirement
        return True

    return False


def player_link_user(path):
    perm = get_permission(path, names=(None, "player", None, None))[0]

    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if player.link_status == LinkStatus.linked:
        if user_link_list(("user", player.link_user, "link", "list")):
            # User meets the privacy requirement
            return True

    return False


def player_link_players(path):
    perm, default = get_permission(path, names=(None, "player", None, None))
    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is viewing a linked player
        return True

    player = Player.query.get(path[1])

    if player.blacklisted:
        # Player is blacklisted
        if not basic_flag(("player", "blacklist", "access")):
            return False

    if perm is True:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if satifies_perm(perm, player.link_privacy, default) <= perm:
        # User meets the privacy requirement
        return True

    return False


def player_settings(path):
    perm, default = get_permission(path, names=(None, "player", None))
    if perm is True:
        # Global permission given
        return True

    user = get_current_user()

    if user and path[1] in user_linked_players(user):
        # User is editing a linked player
        return True

    return False


def match_view(path):
    perm, default = get_permission(path, names=(None, "match", None))
    if perm is True:
        # Global permission given
        return True

    match = Match.query.get(path[1])
    linked_players = user_linked_players(get_current_user())

    for player in match.players:
        if player.player_id in linked_players:
            # User has played in the match
            return True

    return False


def match_players(path):
    perm, default = get_permission(path, names=(None, "match", None))
    if perm is True:
        # Global permission given
        return True

    match = Match.query.get(path[1])
    linked_players = user_linked_players(get_current_user())

    for player in match.players:
        if player.player_id in linked_players:
            # User has played in the match
            return True

    return False


def match_stats(path):
    perm, default = get_permission(path, names=(None, "match", None))
    if perm is True:
        # Global permission given
        return True

    match = Match.query.get(path[1])
    linked_players = user_linked_players(get_current_user())

    threshold = app.config["MATCH_STATS_THRESHOLD"]
    count = 0
    if count < threshold:
        for player in match.players:
            if player.player_id in linked_players:
                # User has played in the match
                count += 1
            elif player_stats_ranked(("player", player.player_id, "stats", "ranked")):
                # Player has public stats
                count += 1

            if count >= threshold:
                # There are enough players in the match with accessable stats to meet the threshold
                return True

    return False


# Permission handlers
handler_map = {
    "user": {
        "list": basic_flag,
        "create": {
            "self": basic_flag,
            "other": basic_flag
        },
        "user": param_wrapper({
            "view": user_view,
            "delete": user_delete,
            "settings": user_settings,
            "role": user_role,
            "password": user_password,
            "link": {
                "list": user_link_list,
                "player": param_wrapper({
                    "add": user_link_add,
                    "remove": user_link_remove
                })
            }
        })
    },
    "player": {
        "list": basic_flag,
        "search": basic_flag,
        "blacklist": {
            "access": basic_flag,
            "view": basic_flag,
            "change": basic_flag
        },
        "player": param_wrapper({
            "view": player_view,
            "region": player_region,
            "leaderboard": player_leaderboard,
            "rankings": player_rankings,
            "stats": {
                "ranked": player_stats_ranked,
                "overall": player_stats_overall,
                "mech": player_stats_mech
            },
            "match": {
                "list": player_match_list,
                "view": player_match_view
            },
            "group": player_group,
            "link": {
                "user": player_link_user,
                "players": player_link_players
            },
            "settings": player_settings
        })
    },
    "match": {
        "list": basic_flag,
        "search": basic_flag,
        "match": param_wrapper({
            "view": match_view,
            "players": match_players,
            "stats": match_stats
        })
    }
    #"group": {
    #    "list": {
    #        "public": group_list_public,
    #        "all": group_list_all
    #    },
    #    "search": group_search,
    #    "group": param_wrapper({
    #        "create": group_create,
    #        "view": group_view,
    #        "edit": group_edit,
    #        "delete": group_delete,
    #        "rankings": group_rankings,
    #        "matches": group_matches,
    #        "member": {
    #            "list": group_member_list,
    #            "player": param_wrapper({
    #                "add": group_member_add,
    #                "invite": group_member_invite,
    #                "join": group_member_join,
    #                "approve": group_member_approve,
    #                "accept": group_member_accept,
    #                "edit": {
    #                    "role": group_member_edit_role,
    #                    "relationship": group_member_edit_relationship
    #                },
    #                "remove": group_member_remove,
    #                "ignore": group_member_ignore,
    #                "block": group_member_block
    #            })
    #        }
    #    })
    #}
}

permissions_view = PermissionView(handler_map)
