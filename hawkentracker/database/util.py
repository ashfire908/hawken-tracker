# -*- coding: utf-8 -*-
# Hawken Tracker - Database Util

from flask.ext.sqlalchemy import get_debug_queries

from hawkentracker.database import db


def dump_queries(name):
    with open("queries-{0}".format(name), "w") as out:
        for query in get_debug_queries():
            out.write("-- Query ({0:.3f}s)\n{1}\nStatement: {2}\n".format(query.duration, query.context, query.statement))
            if isinstance(query.parameters, dict):
                for k, v in sorted(query.parameters.items()):
                    if isinstance(v, str):
                        v = "'" + v + "'"
                    out.write("Param: {0} = {1}\n".format(k, v))
            else:
                for item in query.parameters:
                    out.write("Param: {0}\n".format(item))


def column_windows(session, column, windowsize, begin=None, end=None):
    """Return a series of WHERE clauses against
    a given column that break it into windows.

    Result is an iterable of tuples, consisting of
    ((start, end), whereclause), where (start, end) are the ids.

    Requires a database that supports window functions,
    i.e. Postgresql, SQL Server, Oracle."""
    def window_size(window):
        return session.query(db.func.count(column)).filter(window).one()[0]

    # Base query
    q = session.query(column, db.func.row_number().over(order_by=column).label("rownum")).from_self(column)

    # Set window size
    if windowsize > 1:
        q = q.filter(db.text("rownum %% %d=1" % windowsize))

    # Range filters
    if begin is not None:
        q = q.filter(column >= begin)
    if end is not None:
        q = q.filter(column < end)

    # Get intervals
    intervals = [interval for interval, in q]

    # Constrain intervals
    if begin is not None:
        intervals.insert(0, begin)
    if end is not None:
        intervals.append(end)

    # Generate windows
    windows = []
    while intervals:
        start = intervals.pop(0)
        if len(intervals) > 0:
            windows.append(db.and_(column >= start, column < intervals[0]))
        elif end is None:
            # Only emit if there is no ending point (otherwise the end of the range is not constrained)
            windows.append(column >= start)

    # Remove empty windows
    if begin is not None and len(windows) >= 1 and window_size(windows[0]) == 0:
        windows.pop(0)
    if end is not None and len(windows) >= 1 and window_size(windows[-1]) == 0:
        windows.pop()

    return windows


def windowed_query(q, column, windowsize, begin=None, end=None, streaming=False, chunk_commit=True, journal=None, logger=None, logger_prefix=None):
    """"Break a Query into windows on a given column."""

    def format_log(msg):
        if logger_prefix is not None:
            return logger_prefix + " " + msg
        return msg

    if logger is not None:
        logger.debug(format_log("Generating windows..."))

    windows = column_windows(q.session, column, windowsize, begin=begin, end=end)
    total_windows = len(windows)

    if total_windows == 0:
        if logger is not None:
            logger.debug(format_log("No windows found."))
        return
    elif logger is not None:
        logger.debug(format_log("%d total windows, iterating..."), total_windows)

    i = 0
    if journal is not None:
        i = journal.stage_start(total_windows)
        db.session.commit()

    for whereclause in windows[i:]:
        if streaming:
            for row in q.filter(whereclause).order_by(column):
                yield i, row
        else:
            yield i, q.filter(whereclause).order_by(column).all()

        # Update now so checkpoint will resume correctly, and logging chunk name starts at 1
        i += 1

        if journal is not None:
            journal.stage_checkpoint(i)

        if chunk_commit:
            if logger is not None:
                logger.debug(format_log("Committing chunk %d"), i)
            db.session.commit()

        if logger is not None:
            logger.info(format_log("Chunk %d/%d complete"), i, total_windows)


class NativeIntEnum(db.TypeDecorator):
    """Converts between a native enum and a database integer"""
    impl = db.Integer

    def __init__(self, enum):
        self.enum = enum
        super().__init__()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum(value)


class NativeStringEnum(db.TypeDecorator):
    """Converts between a native enum and a database string"""
    impl = db.String

    def __init__(self, enum):
        self.enum = enum
        super().__init__()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum(value)
