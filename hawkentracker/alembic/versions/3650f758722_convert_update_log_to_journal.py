"""convert update log to journal

Revision ID: 3650f758722
Revises: 55a540177a3
Create Date: 2015-10-24 12:38:53.515983

"""

# revision identifiers, used by Alembic.
revision = "3650f758722"
down_revision = "55a540177a3"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from enum import IntEnum, unique

# Needed tables and mappings
updates = sa.sql.table("updates",
    sa.Column("success", sa.Boolean, nullable=False),
    sa.Column("status", sa.Integer, nullable=False),
    sa.Column("stage", sa.Integer, nullable=False)
)


@unique
class UpdateStatus(IntEnum):
    not_started = 0
    in_progress = 1
    failed = 2
    complete = 3


@unique
class UpdateStage(IntEnum):
    not_started = 0
    complete = 1
    players = 2
    matches = 3
    global_rankings = 4


def upgrade():
    # Rename time and time taken to start and time elapsed
    op.alter_column("updates", "time", new_column_name="start")
    op.alter_column("updates", "time_taken", new_column_name="time_elapsed")

    # Add end time
    # Because upgrading/downgrading would not be safe otherwise, we do not derive the end from start + time_elapsed
    op.add_column("updates", sa.Column("end", sa.DateTime))

    # Add status and progress fields
    op.add_column("updates", sa.Column("status", sa.Integer, nullable=False, index=True, server_default=str(UpdateStatus.not_started.value)))
    op.add_column("updates", sa.Column("stage", sa.Integer, nullable=False, server_default=str(UpdateStage.not_started.value)))
    op.add_column("updates", sa.Column("current_step", sa.Integer))
    op.add_column("updates", sa.Column("total_steps", sa.Integer))

    # Add flags field
    op.add_column("updates", sa.Column("flags", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"))

    # Rename rankings field, add callsigns field
    op.alter_column("updates", "rankings_updated", new_column_name="global_rankings_updated")
    op.add_column("updates", sa.Column("callsigns_updated", sa.Integer, nullable=False, server_default="0"))

    # Remove server defaults (default is to populate the fields initially)
    op.alter_column("updates", "status", server_default=None)
    op.alter_column("updates", "stage", server_default=None)
    op.alter_column("updates", "flags", server_default=None)
    op.alter_column("updates", "callsigns_updated", server_default=None)

    # Convert success bool to status/stage data
    op.execute(
        # Success: False -> Status: Failed, Stage: Not Started
        updates.update().where(updates.c.success.is_(False)).values(status=UpdateStatus.failed.value, stage=UpdateStage.not_started.value)
    )
    op.execute(
        # Success: True -> Status: Complete, Stage: Complete
        updates.update().where(updates.c.success.is_(True)).values(status=UpdateStatus.complete.value, stage=UpdateStage.complete.value)
    )

    # Delete success field
    op.drop_column("updates", "success")


def downgrade():
    # Create success field
    op.add_column("updates", sa.Column("success", sa.Boolean, nullable=False, index=True, server_default="false"))

    # Remove server defaults (default is to populate the fields initially)
    op.alter_column("updates", "success", server_default=None)

    # Convert status data to success bool
    op.execute(
        # Status: Complete -> Success: True
        updates.update().where(updates.c.status == UpdateStatus.complete.value).values(success=True)
    )
    op.execute(
        # Status: Failed -> Success: False
        updates.update().where(updates.c.status == UpdateStatus.failed.value).values(success=False)
    )
    op.execute(
        # Drop anything that isn't explicitly completed or failed, as the log had no concept of this
        updates.delete().where(updates.c.status.notin_((UpdateStatus.complete.value, UpdateStatus.failed.value)))
    )

    # Remove callsigns field, rename rankings field
    op.drop_column("updates", "callsigns_updated")
    op.alter_column("updates", "global_rankings_updated", new_column_name="rankings_updated")

    # Remove flags field
    op.drop_column("updates", "flags")

    # Remove status and progress fields
    op.drop_column("updates", "total_steps")
    op.drop_column("updates", "current_step")
    op.drop_column("updates", "stage")
    op.drop_column("updates", "status")

    # Remove end time
    op.drop_column("updates", "end")

    # Rename time and time taken to start and time elapsed
    op.alter_column("updates", "time_elapsed", new_column_name="time_taken")
    op.alter_column("updates", "start", new_column_name="time")

