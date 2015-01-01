# -*- coding: utf-8 -*-
# Hawken Tracker - Views

from datetime import datetime

from flask import current_app
from hawkentracker.helpers import format_dhms
from hawkentracker.models.database import UpdateLog


@current_app.context_processor
def load_globals():
    update = UpdateLog.last()

    if update is None:
        update = False
    else:
        update = format_dhms((datetime.now() - update).total_seconds())

    return dict(last_update=update)
