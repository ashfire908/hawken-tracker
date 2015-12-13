"""Nullable player stats

Revision ID: 559e6e3b9a2
Revises: 146fda6f2b1
Create Date: 2015-11-22 22:28:48.703819

"""

# revision identifiers, used by Alembic.
revision = "559e6e3b9a2"
down_revision = "146fda6f2b1"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

# Needed tables and mappings
player_stats = sa.sql.table("player_stats",
    sa.Column("abandons", sa.Integer),
    sa.Column("assists", sa.Integer),
    sa.Column("coop_abandon", sa.Integer),
    sa.Column("coop_loss", sa.Integer),
    sa.Column("coop_total", sa.Integer),
    sa.Column("coop_win", sa.Integer),
    sa.Column("cooptdm_abandon", sa.Integer),
    sa.Column("cooptdm_loss", sa.Integer),
    sa.Column("cooptdm_total", sa.Integer),
    sa.Column("cooptdm_win", sa.Integer),
    sa.Column("critical_assists", sa.Integer),
    sa.Column("damage_in", sa.Float),
    sa.Column("damage_out", sa.Float),
    sa.Column("deaths", sa.Integer),
    sa.Column("dm_abandon", sa.Integer),
    sa.Column("dm_loss", sa.Integer),
    sa.Column("dm_mvp", sa.Integer),
    sa.Column("dm_total", sa.Integer),
    sa.Column("dm_win", sa.Integer),
    sa.Column("kill_steals", sa.Integer),
    sa.Column("kills", sa.Integer),
    sa.Column("losses", sa.Integer),
    sa.Column("ma_abandon", sa.Integer),
    sa.Column("ma_loss", sa.Integer),
    sa.Column("ma_total", sa.Integer),
    sa.Column("ma_win", sa.Integer),
    sa.Column("matches", sa.Integer),
    sa.Column("pilot_level", sa.Integer),
    sa.Column("sg_abandon", sa.Integer),
    sa.Column("sg_loss", sa.Integer),
    sa.Column("sg_total", sa.Integer),
    sa.Column("sg_win", sa.Integer),
    sa.Column("tdm_abandon", sa.Integer),
    sa.Column("tdm_loss", sa.Integer),
    sa.Column("tdm_total", sa.Integer),
    sa.Column("tdm_win", sa.Integer),
    sa.Column("time_played", sa.Integer),
    sa.Column("wins", sa.Integer)
)


def upgrade():
    # Allow all stats to be nullable
    op.alter_column("player_stats", "abandons", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "assists", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "coop_abandon", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "coop_loss", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "coop_total", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "coop_win", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "cooptdm_abandon", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "cooptdm_loss", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "cooptdm_total", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "cooptdm_win", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "critical_assists", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "damage_in", existing_type=sa.Float, nullable=True)
    op.alter_column("player_stats", "damage_out", existing_type=sa.Float, nullable=True)
    op.alter_column("player_stats", "deaths", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "dm_abandon", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "dm_loss", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "dm_mvp", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "dm_total", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "dm_win", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "kill_steals", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "kills", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "losses", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "ma_abandon", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "ma_loss", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "ma_total", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "ma_win", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "matches", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "pilot_level", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "sg_abandon", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "sg_loss", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "sg_total", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "sg_win", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "tdm_abandon", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "tdm_loss", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "tdm_total", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "tdm_win", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "time_played", existing_type=sa.Integer, nullable=True)
    op.alter_column("player_stats", "wins", existing_type=sa.Integer, nullable=True)

    # Remove pilot level index
    op.drop_index("ix_player_stats_pilot_level", table_name="player_stats")

    # Null all nullable fields
    op.execute(
        player_stats.update().values(
            abandons=sa.func.nullif(player_stats.c.abandons, 0),
            assists=sa.func.nullif(player_stats.c.assists, 0),
            coop_abandon=sa.func.nullif(player_stats.c.coop_abandon, 0),
            coop_loss=sa.func.nullif(player_stats.c.coop_loss, 0),
            coop_total=sa.func.nullif(player_stats.c.coop_total, 0),
            coop_win=sa.func.nullif(player_stats.c.coop_win, 0),
            cooptdm_abandon=sa.func.nullif(player_stats.c.cooptdm_abandon, 0),
            cooptdm_loss=sa.func.nullif(player_stats.c.cooptdm_loss, 0),
            cooptdm_total=sa.func.nullif(player_stats.c.cooptdm_total, 0),
            cooptdm_win=sa.func.nullif(player_stats.c.cooptdm_win, 0),
            critical_assists=sa.func.nullif(player_stats.c.critical_assists, 0),
            damage_in=sa.func.nullif(player_stats.c.damage_in, 0.0),
            damage_out=sa.func.nullif(player_stats.c.damage_out, 0.0),
            deaths=sa.func.nullif(player_stats.c.deaths, 0),
            dm_abandon=sa.func.nullif(player_stats.c.dm_abandon, 0),
            dm_loss=sa.func.nullif(player_stats.c.dm_loss, 0),
            dm_mvp=sa.func.nullif(player_stats.c.dm_mvp, 0),
            dm_total=sa.func.nullif(player_stats.c.dm_total, 0),
            dm_win=sa.func.nullif(player_stats.c.dm_win, 0),
            kill_steals=sa.func.nullif(player_stats.c.kill_steals, 0),
            kills=sa.func.nullif(player_stats.c.kills, 0),
            losses=sa.func.nullif(player_stats.c.losses, 0),
            ma_abandon=sa.func.nullif(player_stats.c.ma_abandon, 0),
            ma_loss=sa.func.nullif(player_stats.c.ma_loss, 0),
            ma_total=sa.func.nullif(player_stats.c.ma_total, 0),
            ma_win=sa.func.nullif(player_stats.c.ma_win, 0),
            matches=sa.func.nullif(player_stats.c.matches, 0),
            pilot_level=sa.func.nullif(player_stats.c.pilot_level, 0),
            sg_abandon=sa.func.nullif(player_stats.c.sg_abandon, 0),
            sg_loss=sa.func.nullif(player_stats.c.sg_loss, 0),
            sg_total=sa.func.nullif(player_stats.c.sg_total, 0),
            sg_win=sa.func.nullif(player_stats.c.sg_win, 0),
            tdm_abandon=sa.func.nullif(player_stats.c.tdm_abandon, 0),
            tdm_loss=sa.func.nullif(player_stats.c.tdm_loss, 0),
            tdm_total=sa.func.nullif(player_stats.c.tdm_total, 0),
            tdm_win=sa.func.nullif(player_stats.c.tdm_win, 0),
            time_played=sa.func.nullif(player_stats.c.time_played, 0),
            wins=sa.func.nullif(player_stats.c.wins, 0)
        )
    )


def downgrade():
    # Remove null from un-nullable fields
    op.execute(
        player_stats.update().values(
            abandons=sa.func.coalesce(player_stats.c.abandons, 0),
            assists=sa.func.coalesce(player_stats.c.assists, 0),
            coop_abandon=sa.func.coalesce(player_stats.c.coop_abandon, 0),
            coop_loss=sa.func.coalesce(player_stats.c.coop_loss, 0),
            coop_total=sa.func.coalesce(player_stats.c.coop_total, 0),
            coop_win=sa.func.coalesce(player_stats.c.coop_win, 0),
            cooptdm_abandon=sa.func.coalesce(player_stats.c.cooptdm_abandon, 0),
            cooptdm_loss=sa.func.coalesce(player_stats.c.cooptdm_loss, 0),
            cooptdm_total=sa.func.coalesce(player_stats.c.cooptdm_total, 0),
            cooptdm_win=sa.func.coalesce(player_stats.c.cooptdm_win, 0),
            critical_assists=sa.func.coalesce(player_stats.c.critical_assists, 0),
            damage_in=sa.func.coalesce(player_stats.c.damage_in, 0.0),
            damage_out=sa.func.coalesce(player_stats.c.damage_out, 0.0),
            deaths=sa.func.coalesce(player_stats.c.deaths, 0),
            dm_abandon=sa.func.coalesce(player_stats.c.dm_abandon, 0),
            dm_loss=sa.func.coalesce(player_stats.c.dm_loss, 0),
            dm_mvp=sa.func.coalesce(player_stats.c.dm_mvp, 0),
            dm_total=sa.func.coalesce(player_stats.c.dm_total, 0),
            dm_win=sa.func.coalesce(player_stats.c.dm_win, 0),
            kill_steals=sa.func.coalesce(player_stats.c.kill_steals, 0),
            kills=sa.func.coalesce(player_stats.c.kills, 0),
            losses=sa.func.coalesce(player_stats.c.losses, 0),
            ma_abandon=sa.func.coalesce(player_stats.c.ma_abandon, 0),
            ma_loss=sa.func.coalesce(player_stats.c.ma_loss, 0),
            ma_total=sa.func.coalesce(player_stats.c.ma_total, 0),
            ma_win=sa.func.coalesce(player_stats.c.ma_win, 0),
            matches=sa.func.coalesce(player_stats.c.matches, 0),
            pilot_level=sa.func.coalesce(player_stats.c.pilot_level, 0),
            sg_abandon=sa.func.coalesce(player_stats.c.sg_abandon, 0),
            sg_loss=sa.func.coalesce(player_stats.c.sg_loss, 0),
            sg_total=sa.func.coalesce(player_stats.c.sg_total, 0),
            sg_win=sa.func.coalesce(player_stats.c.sg_win, 0),
            tdm_abandon=sa.func.coalesce(player_stats.c.tdm_abandon, 0),
            tdm_loss=sa.func.coalesce(player_stats.c.tdm_loss, 0),
            tdm_total=sa.func.coalesce(player_stats.c.tdm_total, 0),
            tdm_win=sa.func.coalesce(player_stats.c.tdm_win, 0),
            time_played=sa.func.coalesce(player_stats.c.time_played, 0),
            wins=sa.func.coalesce(player_stats.c.wins, 0)
        )
    )

    # Create pilot level index
    op.create_index("ix_player_stats_pilot_level", "player_stats", ["pilot_level"])

    # Disallow some stats to be nullable
    op.alter_column("player_stats", "wins", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "time_played", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "tdm_win", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "tdm_total", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "tdm_loss", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "tdm_abandon", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "sg_win", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "sg_total", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "sg_loss", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "sg_abandon", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "pilot_level", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "matches", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "ma_win", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "ma_total", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "ma_loss", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "ma_abandon", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "losses", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "kills", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "kill_steals", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "dm_win", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "dm_total", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "dm_mvp", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "dm_loss", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "dm_abandon", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "deaths", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "damage_out", existing_type=sa.Float, nullable=False)
    op.alter_column("player_stats", "damage_in", existing_type=sa.Float, nullable=False)
    op.alter_column("player_stats", "critical_assists", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "cooptdm_win", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "cooptdm_total", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "cooptdm_loss", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "cooptdm_abandon", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "coop_win", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "coop_total", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "coop_loss", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "coop_abandon", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "assists", existing_type=sa.Integer, nullable=False)
    op.alter_column("player_stats", "abandons", existing_type=sa.Integer, nullable=False)
