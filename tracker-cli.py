#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Hawken Tracker - CLI interface

import time
import argparse
import logging
from flask.ext.sqlalchemy import get_debug_queries
from hawkentracker import app
from hawkentracker.model import db, PollLog, UpdateLog
from hawkentracker.tracker import poll_servers, update_all


def setup_logging(level):
    logging.basicConfig(format="%(asctime)s %(message)s", level=level)


def dump_queries():
    with open("queries", "w") as out:
        for query in get_debug_queries():
            out.write("-- Query ({0:.3f}s)\nStatement: {1}\n".format(query.duration, query.statement))
            if isinstance(query.parameters, dict):
                for k, v in sorted(query.parameters.items()):
                    if isinstance(v, str):
                        v = "'" + v + "'"
                    out.write("Param: {0} = {1}\n".format(k, v))
            else:
                for item in query.parameters:
                    out.write("Param: {0}\n".format(item))


def main(task, verbosity, force, debug):
    # Setup logging and debugging
    if verbosity == 0:
        setup_logging(logging.ERROR)
    elif verbosity == 1:
        setup_logging(logging.WARNING)
    elif verbosity == 2:
        setup_logging(logging.INFO)
    elif verbosity >= 3:
        setup_logging(logging.DEBUG)

    # Perform the task given
    if task == "setup":
        if verbosity >= 1:
            print("Setting up the database...")

        db.create_all()

        if verbosity >= 1:
            print("Setup complete!")
    elif task == "poll":
        if verbosity >= 1:
            print("Polling servers for players and matches.")
        players, matches = poll_servers()

        if verbosity >= 1:
            print("Updated {0} players and {1} matches.".format(players, matches))
    elif task == "update":
        if verbosity >= 1:
            print("Updating rankings and cached player/match data.")
        players, matches, rankings = update_all(force=force)

        if verbosity >= 1:
            print("Updated {0} players and {1} matches.".format(players, matches))
    elif task == "last":
        poll = PollLog.last()
        update = UpdateLog.last()

        if verbosity == 0:
            poll_time = poll.isoformat() if poll is not None else None
            update_time = update.isoformat() if update is not None else None
            print("{0} {1}".format(poll_time, update_time))
        else:
            print("Last poll: {0}\nLast update: {1}".format(poll, update))

    if debug:
        dump_queries()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track players, matches, and their stats.")
    parser.add_argument("task", choices=("setup", "poll", "update", "last"), help="specifies the task to perform - 'setup' creates the db, 'poll' updates the matches and player info, 'update' updates the player stats, and 'last' gets the last poll time")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument("--force", "-f", action="store_true", default=False)
    parser.add_argument("--debug", action="store_true", default=False)

    args = parser.parse_args()
    with app.app_context():
        main(args.task, verbosity=args.verbose, force=args.force, debug=args.debug)
