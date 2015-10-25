"""Player stats history

Revision ID: 3cd555b6685
Revises: 3bff4bd9d41
Create Date: 2015-10-24 22:40:30.740453

"""

# revision identifiers, used by Alembic.
revision = "3cd555b6685"
down_revision = "3bff4bd9d41"

from alembic import op
import sqlalchemy as sa

player_stats = sa.sql.table("player_stats",
    sa.Column("player_id", sa.String(36), primary_key=True),
    sa.Column("snapshot_taken", sa.DateTime, primary_key=True)
)


def upgrade():
    # Rename last update to snapshot taken
    op.alter_column("player_stats", "last_updated", new_column_name="snapshot_taken")

    # Remove old primary key
    op.drop_constraint("playerstats_pkey", "player_stats", type_="primary")

    # Create new composite primary key
    op.create_primary_key("playerstats_pkey", "player_stats", ["player_id", "snapshot_taken"])

    # Create indexes for player id and snapshot taken
    op.create_index("ix_player_stats_player_id", "player_stats", ["player_id"])
    op.create_index("ix_player_stats_snapshot_taken", "player_stats", ["snapshot_taken"])


def downgrade():
    # Delete all but the latest snapshot for all players
    s1 = player_stats.alias()
    op.execute(
        player_stats.delete().where(player_stats.c.snapshot_taken != sa.select([sa.func.max(s1.c.snapshot_taken)]).where(s1.c.player_id == player_stats.c.player_id))
    )

    # Drop indexes for player id and snapshot taken
    op.drop_index("ix_player_stats_snapshot_taken", table_name="player_stats")
    op.drop_index("ix_player_stats_player_id", table_name="player_stats")

    # Remove composite primary key
    op.drop_constraint("playerstats_pkey", "player_stats", type_="primary")

    # Create original primary key
    op.create_primary_key("playerstats_pkey", "player_stats", ["player_id"])

    # Rename snapshot taken to last update
    op.alter_column("player_stats", "snapshot_taken", new_column_name="last_updated")
