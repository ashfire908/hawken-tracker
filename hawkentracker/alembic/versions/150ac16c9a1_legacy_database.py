"""Original legacy database

Revision ID: 150ac16c9a1
Revises: None
Create Date: 2014-08-10 19:08:56.716973

"""

# revision identifiers, used by Alembic.
revision = "150ac16c9a1"
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Create players table
    op.create_table("players",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("first_seen", sa.DateTime, nullable=False),
        sa.Column("last_seen", sa.DateTime, nullable=False),
        sa.Column("home_region", sa.String),
        sa.Column("common_region", sa.String),
        sa.Column("opt_out", sa.Boolean, nullable=False),
        sa.Column("leaderboard_privacy", sa.Integer),
        sa.Column("rank_privacy", sa.Integer),
        sa.Column("stats_privacy", sa.Integer),
        sa.Column("match_privacy", sa.Integer)
    )

    # Create player stats table
    op.create_table("playerstats",
        sa.Column("player_id", sa.String(36), sa.ForeignKey("players.id"), primary_key=True),
        sa.Column("last_updated", sa.DateTime, nullable=False),
        sa.Column("mmr", sa.Float, nullable=False),
        sa.Column("pilot_level", sa.Integer, nullable=False),
        sa.Column("time_played", sa.Integer, nullable=False),
        sa.Column("xp_per_min", sa.Float),
        sa.Column("hc_per_min", sa.Float),
        sa.Column("kda", sa.Float),
        sa.Column("kill_steals", sa.Float),
        sa.Column("critical_assists", sa.Float),
        sa.Column("damage", sa.Float),
        sa.Column("win_loss", sa.Float),
        sa.Column("dm_win_loss", sa.Float),
        sa.Column("tdm_win_loss", sa.Float),
        sa.Column("ma_win_loss", sa.Float),
        sa.Column("sg_win_loss", sa.Float),
        sa.Column("coop_win_loss", sa.Float),
        sa.Column("cooptdm_win_loss", sa.Float)
    )

    # Create matches table
    op.create_table("matches",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("server_name", sa.String, nullable=False),
        sa.Column("server_region", sa.String, nullable=False),
        sa.Column("server_gametype", sa.String, nullable=False),
        sa.Column("server_map", sa.String, nullable=False),
        sa.Column("server_version", sa.String, nullable=False),
        sa.Column("first_seen", sa.DateTime, nullable=False),
        sa.Column("last_seen", sa.DateTime, nullable=False),
        sa.Column("average_mmr", sa.Float),
        sa.Column("average_level", sa.Float)
    )

    # Create match players table
    op.create_table("matchplayers",
        sa.Column("match_id", sa.String(32), sa.ForeignKey("matches.id"), primary_key=True),
        sa.Column("player_id", sa.String(36), sa.ForeignKey("players.id"), primary_key=True),
        sa.Column("first_seen", sa.DateTime, nullable=False),
        sa.Column("last_seen", sa.DateTime, nullable=False)
    )

    # Create users table
    op.create_table("users",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("username", sa.String, unique=True, nullable=False),
        sa.Column("password", sa.String, nullable=False),
        sa.Column("creation", sa.DateTime, nullable=False),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("email_confirmed", sa.Boolean, nullable=False),
        sa.Column("email_confirm_expires", sa.DateTime),
        sa.Column("email_confirm_token", sa.String),
        sa.Column("type", sa.Integer, nullable=False),
        sa.Column("associated_player", sa.String(36), sa.ForeignKey("players.id"))
    )

    # Create groups table
    op.create_table("groups",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("name", sa.String, unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("website", sa.String),
        sa.Column("invite_only", sa.Boolean, nullable=False),
        sa.Column("listing_privacy", sa.Integer, nullable=False),
        sa.Column("join_privacy", sa.Integer, nullable=False),
        sa.Column("group_privacy", sa.Integer, nullable=False),
        sa.Column("rank_privacy", sa.Integer, nullable=False),
        sa.Column("stats_privacy", sa.Integer, nullable=False),
        sa.Column("match_privacy", sa.Integer, nullable=False)
    )

    # Create group players table
    op.create_table("groupplayers",
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id"), primary_key=True),
        sa.Column("player_id", sa.String(36), sa.ForeignKey("players.id"), primary_key=True),
        sa.Column("role", sa.Integer, nullable=False),
        sa.Column("confirmation", sa.Integer, nullable=False),
        sa.Column("rank_privacy", sa.Integer),
        sa.Column("stats_privacy", sa.Integer),
        sa.Column("match_privacy", sa.Integer)
    )

    # Create polling table
    op.create_table("polls",
        sa.Column("time", sa.DateTime, primary_key=True),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("time_taken", sa.Float, nullable=False),
        sa.Column("players_found", sa.Integer),
        sa.Column("matches_found", sa.Integer)
    )

    # Create updates table
    op.create_table("updates",
        sa.Column("time", sa.DateTime, primary_key=True),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("time_taken", sa.Float, nullable=False),
        sa.Column("players_updated", sa.Integer, nullable=False),
        sa.Column("matches_updated", sa.Integer, nullable=False),
        sa.Column("rankings_updated", sa.Boolean, nullable=False)
    )


def downgrade():
    # Drop tables
    op.drop_table("matchplayers")
    op.drop_table("groupplayers")
    op.drop_table("playerstats")
    op.drop_table("users")
    op.drop_table("groups")
    op.drop_table("matches")
    op.drop_table("players")
    op.drop_table("polls")
    op.drop_table("updates")
