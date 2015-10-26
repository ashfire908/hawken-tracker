#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Hawken Tracker - CLI interface

import sys
import argparse

from hawkentracker import create_app
from hawkentracker.mappings import UpdateFlag, UpdateStatus


def message(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main(task, verbosity, debug, update_flags, resume):
    error = False

    # Import what we need from within the app context
    from hawkentracker.database import db, PollLog, UpdateJournal
    from hawkentracker.database.util import dump_queries
    from hawkentracker.tracker import poll_servers, update_tracker

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
            journal = update_tracker(update_flags, resume=resume)

            if journal.status == UpdateStatus.complete:
                if verbosity >= 1:
                    message("Updated {0} players and {1} matches.".format(journal.players_updated, journal.matches_updated))
            elif journal.status == UpdateStatus.failed:
                if verbosity >= 1:
                    message("Update failed! Please see traceback for more information. Rerun update with resume to retry.")
            else:
                message("Update already in progress!")
                message("Started at {0}, current stage: {1} ({2:.2f}% complete)".format(journal.start, journal.stage.name, journal.stage_progress))

            if journal.status != UpdateStatus.complete:
                error = True

        elif task == "status":
            poll = PollLog.last()
            update = UpdateJournal.last()
            successful_update = UpdateJournal.last_completed()

            if verbosity == 0:
                poll_time = poll.isoformat() if poll is not None else None
                update_time = successful_update.isoformat() if successful_update is not None else None
                message("{0} {1}".format(poll_time, update_time))
            else:
                message("Last poll: {0}".format(poll))
                message("Last successful update: {0}".format(successful_update))
                if update.status != UpdateStatus.complete:
                    if update.status == UpdateStatus.failed:
                        message("Last update was not successful.")
                        message("Started at: {0} (ran for {1} seconds)".format(update.start, update.time_elapsed))
                    else:
                        message("Update currently in progress!")
                        message("Started at: {0} ".format(update.start))
                    message("Status: {0} Stage: {1} ({2:.2f}% complete)".format(update.status.name, update.stage.name, update.stage_progress))
    finally:
        if debug:
            dump_queries(task)

    if error:
        sys.exit(1)


if __name__ == "__main__":
    # Parse args
    parser = argparse.ArgumentParser(description="Tool for managing the tracker (poll servers, update tracker, etc).")
    parser.add_argument("task", choices=("setup", "poll", "update", "status"), help="specifies the task to perform - 'setup' creates the db, 'poll' updates the matches and player info, 'update' updates the player stats, and 'status' shows the poll and update status")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="increase verbosity and log level")
    parser.add_argument("--debug", action="store_true", default=False, help="enable debug mode (forced to off by default)")
    parser.add_argument("--remote-debug", nargs=2, metavar=('host', 'port'), default=False, help="attach to a remote debugger")
    parser.add_argument("--all-players", action="store_true", default=False, help="force updating all players")
    parser.add_argument("--all-matches", action="store_true", default=False, help="force updating all matches")
    parser.add_argument("--update-callsigns", action="store_true", default=False, help="update callsigns during update")
    parser.add_argument("--resume", action="store_true", default=False, help="resumes failed update")

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
    if args.all_players:
        update_flags.append(UpdateFlag.all_players)
    if args.all_matches:
        update_flags.append(UpdateFlag.all_matches)
    if args.update_callsigns:
        update_flags.append(UpdateFlag.update_callsigns)

    # Create app and enter context
    app = create_app(config_parameters=parameters)
    with app.app_context():
        main(args.task, verbosity=args.verbose, debug=args.debug, update_flags=update_flags, resume=args.resume)
