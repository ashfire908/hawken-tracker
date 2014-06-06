#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Hawken Tracker - CLI interface

import argparse
import logging
from hawkentracker import app
from hawkentracker.model import db, PollLog, UpdateLog
from hawkentracker.tracker import poll_servers, update_all


def setup_logging(level):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)


def main(task, verbosity, force):
    # Setup logging and debugging
    debug = False
    if verbosity == 0:
        setup_logging(logging.ERROR)
    elif verbosity == 1:
        setup_logging(logging.WARNING)
    elif verbosity == 2:
        setup_logging(logging.INFO)
    elif verbosity >= 3:
        debug = True
        setup_logging(logging.DEBUG)

    # Perform the task given
    if task == "setup":
        if verbosity >= 1:
            print("Setting up the database...")

        db.create_all()

        if verbosity >= 1:
            print("Setup complete!")
    elif task == "poll":
        players, matches = poll_servers()

        if verbosity >= 1:
            print("Updated {0} players and {1} matches.".format(players, matches))
    elif task == "update":
        players, matches, rankings = update_all(force=force)

        if verbosity >= 1:
            print("Updated {0} players and {1} matches.".format(players, matches))
    elif task == "last":
        poll = PollLog.last()
        update = UpdateLog.last()

        if verbosity == 0:
            print(poll.isoformat() + " " + update.isoformat())
        else:
            print("Last poll: {0}\nLast update: {1}".format(poll, update))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track players, matches, and their stats.")
    parser.add_argument("task", choices=("setup", "poll", "update", "last"), help="specifies the task to perform - 'setup' creates the db, 'poll' updates the matches and player info, 'update' updates the player stats, and 'last' gets the last poll time")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument("--force", "-f", action="store_true", default=False)

    args = parser.parse_args()
    with app.app_context():
        main(args.task, verbosity=args.verbose, force=args.force)
