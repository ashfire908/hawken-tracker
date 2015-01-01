# -*- coding: utf-8 -*-
# Hawken Tracker - Permissions

from functools import wraps
from itertools import count

import types
import logging
from flask import current_app, g
from flask.ext.login import current_user
from hawkenapi.util import copyappend
from hawkentracker.mappings import LinkStatus, default_privacy
from hawkentracker.models.database import User, Player, Match

logger = logging.getLogger(__name__)


def get_permissions():
    user_permissions = g.get("user_permissions", None)
    if user_permissions is None:
        # Build permissions list
        user_role = current_user.role

        if user_role.superadmin:
            # Grant blanket access
            user_permissions = True
        else:
            user_permissions = {}
            for user_perm in user_role.permissions:
                # Collect assigned permissions
                user_permissions[user_perm.permission] = user_perm.power if user_perm.power is not None else True

        g.user_permissions = user_permissions

    return g.user_permissions


class ParamWrapper:
    def __init__(self, map=None):
        if map is None:
            map = {}

        self.map = map

    def __call__(self, path):
        def lookup_argument(argument):
            path.append(argument)
            if isinstance(self.map, dict):
                return PermissionView(self.map, path=path)
            else:
                return self.map(path)

        return lookup_argument

    def __getitem__(self, key):
        return self.map[key]

    def __setitem__(self, key, value):
        self.map[key] = value


class PermissionView:
    def __init__(self, map=None, path=None):
        if map is None:
            map = {}
        if path is None:
            path = []

        self.map = map
        self.path = path

    def __getitem__(self, key):
        target = self.map[key]
        if isinstance(target, ParamWrapper):
            return target(self.path)
        else:
            path = copyappend(self.path, key)
            if isinstance(target, (types.FunctionType, types.MethodType)):
                return target(path)

            return PermissionView(target, path=path)

    def __bool__(self):
        if callable(self.map):
            return self.map(self.path)

        raise ValueError("This permission view cannot be used directly")

    def register_handler(self, handler, path, args, map=None):
        if map is None:
            map = self.map

        key = path.pop(0)
        arg = args.pop(0)

        if len(path) == 0:
            map[key] = handler
        else:
            if key in map:
                if arg:
                    target = map[key].map
                else:
                    target = map[key]
            else:
                if arg:
                    target = ParamWrapper()
                else:
                    target = {}

                map[key] = target

            # Recurse
            self.register_handler(handler, path, args, target)

    __getattr__ = __getitem__


permissions_view = PermissionView()


class PermissionHandler:
    def __init__(self, path, args=None):
        if args is None:
            args = [False] * len(path)

        self.path = path
        self.args = args

    def __call__(self, f):
        @wraps(f)
        def wrapped(path):
            permissions = get_permissions()

            args = []
            # Rebuild args and path for names
            for i, element, arg in zip(count(), path, self.args):
                if arg:
                    # Extract and replace path name
                    args.append(path[i])
                    path[i] = self.path[i]

            # Check for superuser
            if permissions is True:
                power = True
            else:
                # Check for global power
                path = ".".join(path)
                power = get_permissions().get(path, 0)

                if power is not True:
                    # Define real power check
                    def check_power(privacy):
                        if privacy is None:
                            privacy = default_privacy.get(path, None)
                            if privacy is None:
                                raise ValueError("Default power not set but being compared to! Path: {0}".format(".".join(self.path)))

                        return privacy <= power

                    # Wrap function with real power check
                    return f(False, args, check_power)

            # Wrap function with always-true power check
            return f(True, args, self.dummy_power_check)

        # Register handler
        permissions_view.register_handler(wrapped, list(self.path), list(self.args))

        return wrapped

    @staticmethod
    def dummy_power_check(privacy):
        current_app.log.warning("Dummy power check triggered!")
        return True


# Permission handlers
@PermissionHandler(("user", "list"))
def user_list(perm, args, check):
    return perm


@PermissionHandler(("user", "create", "self"))
def user_create_self(perm, args, check):
    return perm


@PermissionHandler(("user", "create", "other"))
def user_create_other(perm, args, check):
    return perm


@PermissionHandler(("user", "user", "view"), (False, True, False))
def user_view(perm, args, check):
    if perm:
        # Global permission given
        return True

    if args[0] == current_user.id:
        # User is viewing themselves
        return True

    if check(User.query.get(args[0]).view_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("user", "user", "delete"), (False, True, False))
def user_delete(perm, args, check):
    if perm:
        # Global permission given
        return True

    if args[0] == current_user.id:
        # User is deleting themselves
        return True

    return False


@PermissionHandler(("user", "user", "settings"), (False, True, False))
def user_settings(perm, args, check):
    if perm:
        # Global permission given
        return True

    if args[0] == current_user.id:
        # User is editing their own settings
        return True

    return False


@PermissionHandler(("user", "user", "role"), (False, True, False))
def user_role(perm, args, check):
    if perm is not True:
        # Global permission not given
        return False

    if args[0] == current_user.id:
        # User is editing their own role
        return False

    return True


@PermissionHandler(("user", "user", "password"), (False, True, False))
def user_password(perm, args, check):
    if perm:
        # Global permission given
        return True

    if args[0] == current_user.id:
        # User is changing their own password
        return True

    return False


@PermissionHandler(("user", "user", "link", "list"), (False, True, False, False))
def user_link_list(perm, args, check):
    if perm:
        # Global permission given
        return True

    if args[0] == current_user.id:
        # User is listing their own linked players
        return True

    if check(User.query.get(args[0]).link_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("user", "user", "link", "player", "add"), (False, True, False, True, False))
def user_link_add(perm, args, check):
    if perm:
        # Global permission given
        return True

    if args[0] == current_user.id:
        # User matches requested user
        player = Player.query.get(args[1])

        if player.link_user == current_user.id and player.link_status == LinkStatus.pending:
            # User is linking against a pending linked player
            return True

    return False


@PermissionHandler(("user", "user", "link", "player", "remove"), (False, True, False, True, False))
def user_link_remove(perm, args, check):
    if perm:
        # Global permission given
        return True

    if args[0] == current_user.id:
        # User matches requested user
        player = Player.query.get(args[1])

        if player.link_user == current_user.id and player.link_status in (LinkStatus.pending, LinkStatus.linked):
            # User is unlinking a pending or linked player
            return True

    return False


@PermissionHandler(("player", "list"))
def player_list(perm, args, check):
    return perm


@PermissionHandler(("player", "search"))
def player_search(perm, args, check):
    return perm


@PermissionHandler(("player", "blacklist", "access"))
def player_blacklist_access(perm, args, check):
    return perm


@PermissionHandler(("player", "blacklist", "view"))
def player_blacklist_view(perm, args, check):
    return perm


@PermissionHandler(("player", "blacklist", "change"))
def player_blacklist_change(perm, args, check):
    return perm


@PermissionHandler(("player", "player", "view"), (False, True, False))
def player_view(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.view_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "region"), (False, True, False))
def player_region(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.region_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "leaderboard"), (False, True, False))
def player_leaderboard(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.leaderboard_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "rankings"), (False, True, False))
def player_rankings(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.leaderboard_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "stats", "ranked"), (False, True, False, False))
def player_stats_ranked(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.ranked_stats_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "stats", "overall"), (False, True, False, False))
def player_stats_overall(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.overall_stats_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "stats", "mech"), (False, True, False, False))
def player_stats_mech(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.mech_stats_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "match", "list"), (False, True, False, False))
def player_match_list(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.match_list_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "match", "match", "view"), (False, True, False, True, False))
def player_match_view(perm, args, check):
    linked_players = current_user.linked_players

    if args[0] in linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.match_view_privacy):
        # User meets the privacy requirement
        return True

    match = Match.query.get(args[1])

    for player in match.players:
        if player.player_id in linked_players:
            # User has played in the match
            return True

    return False


@PermissionHandler(("player", "player", "group"), (False, True, False))
def player_group(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.group_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "link", "user"), (False, True, False, False))
def player_link_user(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if player.link_status == LinkStatus.linked:
        if permissions_view.user.user(player.link_user).link.list:
            # User meets the privacy requirement
            return True

    return False


@PermissionHandler(("player", "player", "link", "players"), (False, True, False, False))
def player_link_players(perm, args, check):
    if args[0] in current_user.linked_players:
        # User is viewing a linked player
        return True

    player = Player.query.get(args[0])

    if player.blacklisted:
        # Player is blacklisted
        if not permissions_view.player.blacklist.access:
            return False

    if perm:
        # Global permission given
        return True

    if player.opt_out:
        # Player has opted out
        return False

    if check(player.link_privacy):
        # User meets the privacy requirement
        return True

    return False


@PermissionHandler(("player", "player", "settings"), (False, True, False))
def player_settings(perm, args, check):
    if perm:
        # Global permission given
        return True

    if args[0] in current_user.linked_players:
        # User is editing a linked player
        return True

    return False


@PermissionHandler(("match", "list"))
def match_list(perm, args, check):
    return perm


@PermissionHandler(("match", "search"))
def match_search(perm, args, check):
    return perm


@PermissionHandler(("match", "match", "view"), (False, True, False))
def match_view(perm, args, check):
    if perm:
        # Global permission given
        return True

    match = Match.query.get(args[0])
    linked_players = current_user.linked_players

    for player in match.players:
        if player.player_id in linked_players:
            # User has played in the match
            return True

    return False


@PermissionHandler(("match", "match", "players"), (False, True, False))
def match_players(perm, args, check):
    if perm:
        # Global permission given
        return True

    match = Match.query.get(args[0])
    linked_players = current_user.linked_players

    for player in match.players:
        if player.player_id in linked_players:
            # User has played in the match
            return True

    return False


@PermissionHandler(("match", "match", "stats"), (False, True, False))
def match_stats(perm, args, check):
    if perm:
        # Global permission given
        return True

    match = Match.query.get(args[0])
    linked_players = current_user.linked_players

    threshold = current_app.config["MATCH_STATS_THRESHOLD"]
    count = 0
    if count < threshold:
        for player in match.players:
            if player.player_id in linked_players:
                # User has played in the match
                count += 1
            elif permissions_view.player.player(player.player_id).stats.ranked:
                # Player has public stats
                count += 1

            if count >= threshold:
                # There are enough players in the match with accessible stats to meet the threshold
                return True

    return False
