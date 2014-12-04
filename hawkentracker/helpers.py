# -*- coding: utf-8 -*-
# Hawken Tracker - Helpers

import re
from datetime import datetime
from functools import wraps
from flask import request, url_for, redirect, g, flash, session
from hawkentracker.account import get_user
from hawkentracker.model import UpdateLog
from hawkentracker.util import format_dhms


def login_required(f):
    @wraps(f)
    def login_check(*args, **kwargs):
        if not session.get("user", False):
            flash("You must be logged in first.", "warning")
            return redirect_to("login")
        return f(*args, **kwargs)
    return login_check


def access_denied(message):
    flash("Access denied - {0}".format(message), "error")
    return to_last()


def redirect_to(target):
    return redirect(url_for(target, next=request.endpoint))


def to_next(default="index"):
    next = request.args.get("next", default)
    if next == request.endpoint or next == "":
        return redirect(url_for(default))
    return redirect(url_for(next))


def to_last():
    # Finish implmenting
    return redirect(url_for("leaderboard.index"))


def format_stat(stat, field):
    if field in ("mmr", "xp_per_min", "hc_per_min", "kda", "damage", "win_loss", "dm_win_loss", "tdm_win_loss", "ma_win_loss", "sg_win_loss", "coop_win_loss", "cooptdm_win_loss"):
        return "{0:.2f}".format(stat)
    if field in ("kill_steals", "critical_assists"):
        return "{0:.2f}%".format(stat * 100)
    if field == "time_played":
        return format_dhms(stat)

    return stat


def parse_serverside(form):
    # FIXME: I have no idea what this does, please document
    output = {}
    args = re.compile(r"\[([^\[\]]+)\]")

    def insert(cur, list, value):
        if len(list) == 1:
            cur[list[0]] = value
            return
        if not list[0] in cur:
            cur[list[0]] = {}
        insert(cur[list[0]], list[1:], value)

    for k, v in form.items():
        try:
            keys = [k[:k.index("[")]]
        except ValueError:
            output[k] = v
        else:
            keys.extend(args.findall(k))
            insert(output, keys, v)

    return output


def load_globals():
    update = g.get("since_update", None)
    if update is None:
        update = UpdateLog.last()

        if update is None:
            g.since_update = False
        else:
            g.since_update = format_dhms((datetime.now() - update).total_seconds())

    user_name = g.get("user_name", None)
    if user_name is None:
        user = get_user()

        g.user_name = user.username if user is not None else False
