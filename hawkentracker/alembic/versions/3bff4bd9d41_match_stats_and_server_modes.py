"""Match stats and server modes

Revision ID: 3bff4bd9d41
Revises: 3650f758722
Create Date: 2015-10-24 21:29:41.998811

"""

# revision identifiers, used by Alembic.
revision = "3bff4bd9d41"
down_revision = "3650f758722"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add boolean mode fields
    op.add_column("matches", sa.Column("server_matchmaking", sa.Boolean))
    op.add_column("matches", sa.Column("server_tournament", sa.Boolean))
    op.add_column("matches", sa.Column("server_password_protected", sa.Boolean))
    op.add_column("matches", sa.Column("server_mmr_ignored", sa.Boolean))

    # Rename average fields
    op.alter_column("matches", "average_level", new_column_name="pilot_level_avg")
    op.alter_column("matches", "average_mmr", new_column_name="mmr_avg")

    # Add new stat fields
    op.add_column("matches", sa.Column("mmr_max", sa.Float))
    op.add_column("matches", sa.Column("mmr_min", sa.Float))
    op.add_column("matches", sa.Column("mmr_stddev", sa.Float))

    # Add stats update field
    op.add_column("matches", sa.Column("last_stats_update", sa.DateTime))


def downgrade():
    # Remove stats update field
    op.drop_column("matches", "last_stats_update")

    # Remove stat fields
    op.drop_column("matches", "mmr_stddev")
    op.drop_column("matches", "mmr_min")
    op.drop_column("matches", "mmr_max")

    # Rename average fields
    op.alter_column("matches", "pilot_level_avg", new_column_name="average_level")
    op.alter_column("matches", "mmr_avg", new_column_name="average_mmr")

    # Remove boolean mode fields
    op.drop_column("matches", "server_mmr_ignored")
    op.drop_column("matches", "server_password_protected")
    op.drop_column("matches", "server_tournament")
    op.drop_column("matches", "server_matchmaking")
