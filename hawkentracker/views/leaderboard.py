# -*- coding: utf-8 -*-
# Hawken Tracker - Leaderboard views

from flask import Blueprint, render_template

from hawkentracker.mappings import ranking_fields, ranking_names

leaderboard = Blueprint("leaderboard", __name__)


@leaderboard.route("/")
def index():
    context = {
        "sort_fields": ranking_fields,
        "sort_names": ranking_names,
        "default_sort": "mmr"
    }

    return render_template("leaderboard/index.jade", **context)
