# -*- coding: utf-8 -*-
# Hawken Tracker

from flask import Flask

from hawkentracker.config import load_config, setup_logging


def create_app(config_filename=None, config_parameters=None):
    # Create application
    app = Flask("hawkentracker", instance_relative_config=True)

    # Setup config
    load_config(app, config_filename, config_parameters)

    # Setup logging
    setup_logging(app)

    # Setup extensions
    app.jinja_env.add_extension("pyjade.ext.jinja.PyJadeExtension")

    # Setup model
    from hawkentracker.database import db
    db.init_app(app)

    # Use app context while setting up session and views
    with app.app_context():
        # Setup views
        from hawkentracker.views.api import api
        from hawkentracker.views.leaderboard import leaderboard
        from hawkentracker.views.match import match
        from hawkentracker.views.player import player
        app.register_blueprint(api)
        app.register_blueprint(leaderboard)
        app.register_blueprint(match)
        app.register_blueprint(player)

    # Return app
    return app
