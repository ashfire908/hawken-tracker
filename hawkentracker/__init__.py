# -*- coding: utf-8 -*-
# Hawken Tracker

# Create the application
from flask import Flask
app = Flask(__name__, instance_relative_config=True)
app.jinja_env.add_extension("pyjade.ext.jinja.PyJadeExtension")

# Pull in the config
import hawkentracker.config
