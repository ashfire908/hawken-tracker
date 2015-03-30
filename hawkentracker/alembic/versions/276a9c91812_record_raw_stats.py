"""Record raw stats

Revision ID: 276a9c91812
Revises: 28f5d71c07f
Create Date: 2015-03-30 01:27:58.532340

"""

# revision identifiers, used by Alembic.
revision = "276a9c91812"
down_revision = "28f5d71c07f"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Drop old indexes
    op.drop_index("ix_player_stats_critical_assists", table_name="player_stats")
    op.drop_index("ix_player_stats_damage", table_name="player_stats")
    op.drop_index("ix_player_stats_kill_steals", table_name="player_stats")

    # Rename ranked stat fields
    op.alter_column("player_stats", "kill_steals", new_column_name="kill_steal_ratio")
    op.alter_column("player_stats", "critical_assists", new_column_name="critical_assist_ratio")
    op.alter_column("player_stats", "damage", new_column_name="damage_ratio")

    # Add new stats fields
    op.add_column("player_stats", sa.Column("kills", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("deaths", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("assists", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("kill_steals", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("critical_assists", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("damage_in", sa.Float, nullable=False, server_default="0.0"))
    op.add_column("player_stats", sa.Column("damage_out", sa.Float, nullable=False, server_default="0.0"))
    op.add_column("player_stats", sa.Column("matches", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("wins", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("losses", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("abandons", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("dm_total", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("dm_win", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("dm_mvp", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("dm_loss", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("dm_abandon", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("tdm_total", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("tdm_win", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("tdm_loss", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("tdm_abandon", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("ma_total", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("ma_win", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("ma_loss", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("ma_abandon", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("sg_total", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("sg_win", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("sg_loss", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("sg_abandon", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("coop_total", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("coop_win", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("coop_loss", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("coop_abandon", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("cooptdm_total", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("cooptdm_win", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("cooptdm_loss", sa.Integer, nullable=False, server_default="0"))
    op.add_column("player_stats", sa.Column("cooptdm_abandon", sa.Integer, nullable=False, server_default="0"))

    # Remove server defaults for new stats fields (default is to populate the fields initially)
    op.alter_column("player_stats", "kills", server_default=None)
    op.alter_column("player_stats", "deaths", server_default=None)
    op.alter_column("player_stats", "assists", server_default=None)
    op.alter_column("player_stats", "kill_steals", server_default=None)
    op.alter_column("player_stats", "critical_assists", server_default=None)
    op.alter_column("player_stats", "damage_in", server_default=None)
    op.alter_column("player_stats", "damage_out", server_default=None)
    op.alter_column("player_stats", "matches", server_default=None)
    op.alter_column("player_stats", "wins", server_default=None)
    op.alter_column("player_stats", "losses", server_default=None)
    op.alter_column("player_stats", "abandons", server_default=None)
    op.alter_column("player_stats", "dm_total", server_default=None)
    op.alter_column("player_stats", "dm_win", server_default=None)
    op.alter_column("player_stats", "dm_mvp", server_default=None)
    op.alter_column("player_stats", "dm_loss", server_default=None)
    op.alter_column("player_stats", "dm_abandon", server_default=None)
    op.alter_column("player_stats", "tdm_total", server_default=None)
    op.alter_column("player_stats", "tdm_win", server_default=None)
    op.alter_column("player_stats", "tdm_loss", server_default=None)
    op.alter_column("player_stats", "tdm_abandon", server_default=None)
    op.alter_column("player_stats", "ma_total", server_default=None)
    op.alter_column("player_stats", "ma_win", server_default=None)
    op.alter_column("player_stats", "ma_loss", server_default=None)
    op.alter_column("player_stats", "ma_abandon", server_default=None)
    op.alter_column("player_stats", "sg_total", server_default=None)
    op.alter_column("player_stats", "sg_win", server_default=None)
    op.alter_column("player_stats", "sg_loss", server_default=None)
    op.alter_column("player_stats", "sg_abandon", server_default=None)
    op.alter_column("player_stats", "coop_total", server_default=None)
    op.alter_column("player_stats", "coop_win", server_default=None)
    op.alter_column("player_stats", "coop_loss", server_default=None)
    op.alter_column("player_stats", "coop_abandon", server_default=None)
    op.alter_column("player_stats", "cooptdm_total", server_default=None)
    op.alter_column("player_stats", "cooptdm_win", server_default=None)
    op.alter_column("player_stats", "cooptdm_loss", server_default=None)
    op.alter_column("player_stats", "cooptdm_abandon", server_default=None)

    # Add new indexes
    op.create_index(op.f("ix_player_stats_critical_assist_ratio"), "player_stats", ["critical_assist_ratio"])
    op.create_index(op.f("ix_player_stats_damage_ratio"), "player_stats", ["damage_ratio"])
    op.create_index(op.f("ix_player_stats_kill_steal_ratio"), "player_stats", ["kill_steal_ratio"])


def downgrade():
    # Drop new indexes
    op.drop_index("ix_player_stats_critical_assist_ratio", table_name="player_stats")
    op.drop_index("ix_player_stats_damage_ratio", table_name="player_stats")
    op.drop_index("ix_player_stats_kill_steal_ratio", table_name="player_stats")

    # Drop new stats fields
    op.drop_column("player_stats", "kills")
    op.drop_column("player_stats", "deaths")
    op.drop_column("player_stats", "assists")
    op.drop_column("player_stats", "kill_steals")
    op.drop_column("player_stats", "critical_assists")
    op.drop_column("player_stats", "damage_in")
    op.drop_column("player_stats", "damage_out")
    op.drop_column("player_stats", "matches")
    op.drop_column("player_stats", "wins")
    op.drop_column("player_stats", "losses")
    op.drop_column("player_stats", "abandons")
    op.drop_column("player_stats", "dm_total")
    op.drop_column("player_stats", "dm_win")
    op.drop_column("player_stats", "dm_mvp")
    op.drop_column("player_stats", "dm_loss")
    op.drop_column("player_stats", "dm_abandon")
    op.drop_column("player_stats", "tdm_total")
    op.drop_column("player_stats", "tdm_win")
    op.drop_column("player_stats", "tdm_loss")
    op.drop_column("player_stats", "tdm_abandon")
    op.drop_column("player_stats", "ma_total")
    op.drop_column("player_stats", "ma_win")
    op.drop_column("player_stats", "ma_loss")
    op.drop_column("player_stats", "ma_abandon")
    op.drop_column("player_stats", "sg_total")
    op.drop_column("player_stats", "sg_win")
    op.drop_column("player_stats", "sg_loss")
    op.drop_column("player_stats", "sg_abandon")
    op.drop_column("player_stats", "coop_total")
    op.drop_column("player_stats", "coop_win")
    op.drop_column("player_stats", "coop_loss")
    op.drop_column("player_stats", "coop_abandon")
    op.drop_column("player_stats", "cooptdm_total")
    op.drop_column("player_stats", "cooptdm_win")
    op.drop_column("player_stats", "cooptdm_loss")
    op.drop_column("player_stats", "cooptdm_abandon")

    # Rename ranked stat fields
    op.alter_column("player_stats", "kill_steal_ratio", new_column_name="kill_steals")
    op.alter_column("player_stats", "damage_ratio", new_column_name="damage")
    op.alter_column("player_stats", "critical_assist_ratio", new_column_name="critical_assists")

    # Create old indexes
    op.create_index(op.f("ix_player_stats_kill_steals"), "player_stats", ["kill_steals"])
    op.create_index(op.f("ix_player_stats_critical_assists"), "player_stats", ["critical_assists"])
    op.create_index(op.f("ix_player_stats_damage"), "player_stats", ["damage"])
