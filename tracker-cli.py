#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Hawken Tracker - CLI interface

import sys
import argparse
from hawkentracker import create_app
from hawkentracker.mappings import UpdateFlag


def message(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main(task, verbosity, debug, update_flags):
    # Import what we need from within the app context
    from hawkentracker.models.database import db, PollLog, UpdateLog, dump_queries
    from hawkentracker.tracker import poll_servers, update_tracker, update_callsigns

    try:
        # Perform the task given
        if task == "setup":
            if verbosity >= 1:
                message("Setting up the database...")

            db.create_all()

            if verbosity >= 1:
                message("Setup complete!")
        elif task == "poll":
            if verbosity >= 1:
                message("Polling servers for players and matches.")
            players, matches = poll_servers()

            if verbosity >= 1:
                message("Updated {0} players and {1} matches.".format(players, matches))
        elif task == "update":
            if verbosity >= 1:
                message("Updating rankings and cached player/match data.")
            players, matches, rankings = update_tracker(update_flags)

            if verbosity >= 1:
                message("Updated {0} players and {1} matches.".format(players, matches))
        elif task == "last":
            poll = PollLog.last()
            update = UpdateLog.last()

            if verbosity == 0:
                poll_time = poll.isoformat() if poll is not None else None
                update_time = update.isoformat() if update is not None else None
                message("{0} {1}".format(poll_time, update_time))
            else:
                message("Last poll: {0}\nLast update: {1}".format(poll, update))
        elif task == "callsigns":
            if verbosity >= 1:
                message("Updating tracked player callsigns.")

            players = update_callsigns()

            if verbosity >= 1:
                message("Updated callsigns for {0} players.".format(players))
    finally:
        if debug:
            dump_queries(task)


if __name__ == "__main__":
    # Parse args
    parser = argparse.ArgumentParser(description="Tool for managing the tracker (poll servers, update tracker, etc).")
    parser.add_argument("task", choices=("setup", "poll", "update", "last", "callsigns"), help="specifies the task to perform - 'setup' creates the db, 'poll' updates the matches and player info, 'update' updates the player stats, 'last' gets the last poll time, and 'callsigns' populates player callsigns")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="increase verbosity and log level")
    parser.add_argument("--debug", action="store_true", default=False, help="enable debug mode (forced to off by default)")
    parser.add_argument("--remote-debug", nargs=2, metavar=('host', 'port'), default=False, help="attach to a remote debugger")
    parser.add_argument("--update-players", action="store_true", default=False, help="force updating all players")
    parser.add_argument("--update-matches", action="store_true", default=False, help="force updating all matches")
    parser.add_argument("--update-callsigns", action="store_true", default=False, help="force updating all callsigns")

    args = parser.parse_args()

    if args.remote_debug:
        # Setup remote debugging
        host, port = args.remote_debug

        import pydevd
        pydevd.settrace(host, port=int(port), stdoutToServer=True, stderrToServer=True, suspend=False)

    # Setup config parameters
    parameters = {}

    if args.verbose == 0:
        parameters["LOG_LEVEL"] = "ERROR"
    elif args.verbose == 1:
        parameters["LOG_LEVEL"] = "WARNING"
    elif args.verbose == 2:
        parameters["LOG_LEVEL"] = "INFO"
    elif args.verbose >= 3:
        parameters["LOG_LEVEL"] = "DEBUG"

    parameters["DEBUG"] = args.debug

    update_flags = []
    if args.update_players:
        update_flags.append(UpdateFlag.players)
    if args.update_matches:
        update_flags.append(UpdateFlag.matches)
    if args.update_callsigns:
        update_flags.append(UpdateFlag.callsigns)

    # Create app and enter context
    app = create_app(config_parameters=parameters)
    with app.app_context():
        main(args.task, verbosity=args.verbose, debug=args.debug, update_flags=update_flags)
