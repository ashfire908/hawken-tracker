"""Player latest snapshot

Revision ID: 146fda6f2b1
Revises: 4810939400a
Create Date: 2015-11-22 19:54:57.979302

"""

# revision identifiers, used by Alembic.
revision = "146fda6f2b1"
down_revision = "4810939400a"
branch_labels = ("ranking_history",)
depends_on = None

from alembic import op
import sqlalchemy as sa

# Needed tables and mappings
players = sa.sql.table("players",
    sa.Column("player_id", sa.String(36), primary_key=True),
    sa.Column("latest_snapshot", sa.DateTime)
)
player_stats = sa.sql.table("player_stats",
    sa.Column("player_id", sa.String(36), sa.ForeignKey('players.player_id'), primary_key=True),
    sa.Column("snapshot_taken", sa.DateTime, primary_key=True)
)


def upgrade():
    op.add_column("players", sa.Column("latest_snapshot", sa.DateTime))

    latest_snapshot = sa.select([sa.func.max(player_stats.c.snapshot_taken)]).\
        where(players.c.player_id == player_stats.c.player_id)

    # Populate snapshot field
    op.execute(
        players.update().values(latest_snapshot=latest_snapshot)
    )


def downgrade():
    op.drop_column("players", "latest_snapshot")
