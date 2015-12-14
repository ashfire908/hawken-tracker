"""Ranking history

Revision ID: 45db998ac3b
Revises: 559e6e3b9a2
Create Date: 2015-12-13 18:02:50.743927

"""

# revision identifiers, used by Alembic.
revision = "45db998ac3b"
down_revision = "559e6e3b9a2"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Create player ranking snapshots table
    op.create_table("player_ranking_snapshots",
        sa.Column("snapshot_taken", sa.DateTime, primary_key=True),
        sa.Column("mmr", sa.Integer),
        sa.Column("time_played", sa.Integer),
        sa.Column("xp", sa.Integer),
        sa.Column("xp_per_min", sa.Integer),
        sa.Column("hc", sa.Integer),
        sa.Column("hc_per_min", sa.Integer),
        sa.Column("kda", sa.Integer),
        sa.Column("kill_steal_ratio", sa.Integer),
        sa.Column("critical_assist_ratio", sa.Integer),
        sa.Column("damage_ratio", sa.Integer),
        sa.Column("win_loss", sa.Integer),
        sa.Column("dm_win_loss", sa.Integer),
        sa.Column("tdm_win_loss", sa.Integer),
        sa.Column("ma_win_loss", sa.Integer),
        sa.Column("sg_win_loss", sa.Integer),
        sa.Column("coop_win_loss", sa.Integer),
        sa.Column("cooptdm_win_loss", sa.Integer)
    )

    # Create player rankings table
    op.create_table("player_rankings",
        sa.Column("player_id", sa.String(length=36), sa.ForeignKey("players.player_id"), primary_key=True, index=True),
        sa.Column("snapshot_taken", sa.DateTime(), sa.ForeignKey("player_ranking_snapshots.snapshot_taken"), primary_key=True, index=True),
        sa.Column("mmr", sa.Integer, index=True),
        sa.Column("time_played", sa.Integer, index=True),
        sa.Column("xp", sa.Integer, index=True),
        sa.Column("xp_per_min", sa.Integer, index=True),
        sa.Column("hc", sa.Integer, index=True),
        sa.Column("hc_per_min", sa.Integer, index=True),
        sa.Column("kda", sa.Integer, index=True),
        sa.Column("kill_steal_ratio", sa.Integer, index=True),
        sa.Column("critical_assist_ratio", sa.Integer, index=True),
        sa.Column("damage_ratio", sa.Integer, index=True),
        sa.Column("win_loss", sa.Integer, index=True),
        sa.Column("dm_win_loss", sa.Integer, index=True),
        sa.Column("tdm_win_loss", sa.Integer, index=True),
        sa.Column("ma_win_loss", sa.Integer, index=True),
        sa.Column("sg_win_loss", sa.Integer, index=True),
        sa.Column("coop_win_loss", sa.Integer, index=True),
        sa.Column("cooptdm_win_loss", sa.Integer, index=True)
    )


def downgrade():
    # Drop player rankings table
    op.drop_table("player_rankings")

    # Drop player ranking snapshots table
    op.drop_table("player_ranking_snapshots")
