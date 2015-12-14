# -*- coding: utf-8 -*-
# Hawken Tracker - Views

from datetime import datetime

from flask import current_app

from hawkentracker.helpers import format_dhms
from hawkentracker.database import UpdateJournal


@current_app.context_processor
def load_globals():
    update = UpdateJournal.last_completed()

    if update is None:
        update = False
    else:
        update = format_dhms((datetime.utcnow() - update.start).total_seconds())

    return dict(last_update=update)
