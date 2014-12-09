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
    from hawkentracker.model import db
    db.init_app(app)

    # Setup mailer
    from hawkentracker.mailer import mail
    mail.init_app(app)

    # Use app context while setting up views
    with app.app_context():
        # Setup views
        from hawkentracker.views.account import account
        from hawkentracker.views.auth import auth
        from hawkentracker.views.data import data
        from hawkentracker.views.leaderboard import leaderboard
        from hawkentracker.views.match import match
        from hawkentracker.views.player import player
        from hawkentracker.views.user import user
        app.register_blueprint(account)
        app.register_blueprint(auth)
        app.register_blueprint(data)
        app.register_blueprint(leaderboard)
        app.register_blueprint(match)
        app.register_blueprint(player)
        app.register_blueprint(user)

    # Return app
    return app
