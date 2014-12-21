# -*- coding: utf-8 -*-
# Hawken Tracker - Helpers

import re

from flask import request, url_for, redirect, flash


def access_denied(message):
    flash("Access denied - {0}".format(message), "error")
    return to_last()


def redirect_to(target):
    return redirect(url_for(target, next=request.endpoint))


def to_index():
    return redirect(url_for("leaderboard.index"))


def to_next(default="index"):
    next = request.args.get("next", default)
    if next == request.endpoint or next == "":
        return redirect(url_for(default))
    return redirect(url_for(next))


def to_last():
    # Finish implmenting
    to_index()


def format_dhms(seconds, skip=0):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if skip > 0:
        seconds = 0
        if skip > 1:
            minutes = 0
            if skip > 2:
                hours = 0
                # I'm not skipping days.
    output = []
    if days != 0:
        if days > 1:
            output.append("{} days".format(days))
        else:
            output.append("{} day".format(days))
    if hours != 0:
        if hours > 1:
            output.append("{} hours".format(hours))
        else:
            output.append("{} hour".format(hours))
    if minutes != 0:
        if minutes > 1:
            output.append("{} minutes".format(minutes))
        else:
            output.append("{} minute".format(minutes))
    if seconds != 0:
        if seconds > 1:
            output.append("{} seconds".format(seconds))
        else:
            output.append("{} second".format(seconds))
    return " ".join(output)


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
