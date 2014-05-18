# -*- coding: utf-8 -*-
# Hawken Tracker - Application

import sys
import argparse
import logging
import json
from hawkentracker.tracker import HawkenTracker


def setup_logging(level):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)


def main(task, verbosity):
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

    # Open up the Tracker
    config = json.load(open("config.json"))
    tracker = HawkenTracker(config["db_url"], config["api_username"], config["api_password"], debug=debug)

    # Perform the task given
    if task == "setup":
        if verbosity >= 1:
            print("Setting up the database...")

        tracker.setup_db()

        if verbosity >= 1:
            print("Setup complete!")
    elif task == "poll":
        players, matches = tracker.poll_players()

        if verbosity >= 1:
            print("Updated {0} players and {1} matches.".format(players, matches))
    elif task == "update":
        players = tracker.stats_update()

        if verbosity >= 1:
            print("Updated stats for {0} players.".format(players))
    elif task == "last":
        with tracker.get_session() as session:
            poll = tracker.last_poll(session)
            update = tracker.last_update(session)

        if verbosity == 0:
            print(poll.isoformat() + " " + update.isoformat())
        else:
            print("Last poll: {0}\nLast update: {1}".format(poll, update))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track players, matches, and their stats.")
    parser.add_argument("task", choices=("setup", "poll", "update", "last"), help="specifies the task to perform - 'setup' creates the db, 'poll' updates the matches and player info, 'update' updates the player stats, and 'last' gets the last poll time")
    parser.add_argument("--verbose", "-v", action="count", default=0)

    args = parser.parse_args()
    main(args.task, verbosity=args.verbose)
