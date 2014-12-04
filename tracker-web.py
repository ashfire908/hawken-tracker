#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from hawkentracker import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runs a server for the tracker web interface")
    parser.add_argument("--host", help="sets the host to listen for")
    parser.add_argument("--port", type=int, help="sets the port to listen for")
    parser.add_argument("--debug", action="store_true", default=None)

    args = parser.parse_args()

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)
