"""Convert poll log to journal

Revision ID: 4810939400a
Revises: 593f1ba4670
Create Date: 2015-11-15 23:55:10.626782

"""

# revision identifiers, used by Alembic.
revision = "4810939400a"
down_revision = "593f1ba4670"
branch_labels = ("poll_journal",)
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from enum import IntEnum, unique

# Needed tables and mappings
polls = sa.sql.table("polls",
    sa.Column("success", sa.Boolean, nullable=False),
    sa.Column("status", sa.Integer, nullable=False),
    sa.Column("stage", sa.Integer, nullable=False),
    sa.Column("players_added", sa.Integer),
    sa.Column("players_updated", sa.Integer),
    sa.Column("matches_added", sa.Integer),
    sa.Column("matches_updated", sa.Integer)
)


@unique
class PollStatus(IntEnum):
    not_started = 0
    in_progress = 1
    failed = 2
    complete = 3


@unique
class PollStage(IntEnum):
    not_started = 0
    complete = 1
    fetch_servers = 2
    players = 3
    matches = 4


def upgrade():
    # Rename time and time taken to start and time elapsed
    op.alter_column("polls", "time", new_column_name="start")
    op.alter_column("polls", "time_taken", new_column_name="time_elapsed")

    # Add end time
    # Because upgrading/downgrading would not be safe otherwise, we do not derive the end from start + time_elapsed
    op.add_column("polls", sa.Column("end", sa.DateTime))

    # Add status and progress fields
    op.add_column("polls", sa.Column("status", sa.Integer, nullable=False, index=True, server_default=str(PollStatus.not_started.value)))
    op.add_column("polls", sa.Column("stage", sa.Integer, nullable=False, server_default=str(PollStage.not_started.value)))

    # Add flags field
    op.add_column("polls", sa.Column("flags", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"))

    # Rename updated fields, add added fields
    op.alter_column("polls", "players_found", new_column_name="players_updated")
    op.alter_column("polls", "matches_found", new_column_name="matches_updated")
    op.add_column("polls", sa.Column("players_added", sa.Integer))
    op.add_column("polls", sa.Column("matches_added", sa.Integer))

    # Remove server defaults (default is to populate the fields initially)
    op.alter_column("polls", "status", server_default=None)
    op.alter_column("polls", "stage", server_default=None)
    op.alter_column("polls", "flags", server_default=None)

    # Convert success bool to status/stage data
    op.execute(
        # Success: False -> Status: Failed, Stage: Not Started
        polls.update().where(polls.c.success.is_(False)).values(status=PollStatus.failed.value, stage=PollStage.not_started.value)
    )
    op.execute(
        # Success: True -> Status: Complete, Stage: Complete
        polls.update().where(polls.c.success.is_(True)).values(status=PollStatus.complete.value, stage=PollStage.complete.value)
    )

    # Delete success field
    op.drop_column("polls", "success")


def downgrade():
    # Create success field
    op.add_column("polls", sa.Column("success", sa.Boolean, nullable=False, index=True, server_default="false"))

    # Remove server defaults (default is to populate the fields initially)
    op.alter_column("polls", "success", server_default=None)

    # Convert status data to success bool
    op.execute(
        # Status: Complete -> Success: True
        polls.update().where(polls.c.status == PollStatus.complete.value).values(success=True)
    )
    op.execute(
        # Status: Failed -> Success: False
        polls.update().where(polls.c.status == PollStatus.failed.value).values(success=False)
    )
    op.execute(
        # Drop anything that isn't explicitly completed or failed, as the log had no concept of this
        polls.delete().where(polls.c.status.notin_((PollStatus.complete.value, PollStatus.failed.value)))
    )

    # Combine added and updated values
    op.execute(
        polls.update().where(polls.c.players_added.isnot(None)).values(players_updated=(polls.c.players_added + polls.c.players_updated))
    )
    op.execute(
        polls.update().where(polls.c.matches_added.isnot(None)).values(matches_updated=(polls.c.matches_added + polls.c.matches_updated))
    )

    # Remove added fields, rename updated fields
    op.drop_column("polls", "matches_added")
    op.drop_column("polls", "players_added")
    op.alter_column("polls", "matches_updated", new_column_name="matches_found")
    op.alter_column("polls", "players_updated", new_column_name="players_found")

    # Remove flags field
    op.drop_column("polls", "flags")

    # Add status and progress fields
    op.drop_column("polls", "stage")
    op.drop_column("polls", "status")

    # Remove end time
    op.drop_column("polls", "end")

    # Rename time and time taken to start and time elapsed
    op.alter_column("polls", "time_elapsed", new_column_name="time_taken")
    op.alter_column("polls", "start", new_column_name="time")
