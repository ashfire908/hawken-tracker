#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import logging
import argparse
from hawkentracker import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runs a server for the tracker web interface")
    parser.add_argument("--host", help="sets the host to listen for")
    parser.add_argument("--port", type=int, help="sets the port to listen for")
    parser.add_argument("--debug", action="store_true", default=None)

    args = parser.parse_args()
    opts = {}

    app = create_app()

    # I call hax.
    for frame in inspect.stack():
        if frame[1].endswith("pydevd.py"):
            logging.info("External debugger detected. Disabling reloader.")
            opts["use_reloader"] = False
            break

    app.run(host=args.host, port=args.port, debug=args.debug, **opts)

