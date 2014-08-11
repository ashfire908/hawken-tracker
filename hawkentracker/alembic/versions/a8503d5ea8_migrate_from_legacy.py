"""Migrate from legacy schema

Revision ID: a8503d5ea8
Revises: 1a885a00b52
Create Date: 2014-08-10 23:12:23.675443

"""

# revision identifiers, used by Alembic.
revision = "a8503d5ea8"
down_revision = "1a885a00b52"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Drop group tables
    op.drop_table("groupplayers")
    op.drop_table("groups")

    # Rename tables
    op.rename_table("matchplayers", "match_players")
    op.rename_table("playerstats", "player_stats")

    # Add indexes for match players
    op.create_index(op.f("ix_match_players_match_id"), "match_players", ["match_id"])
    op.create_index(op.f("ix_match_players_player_id"), "match_players", ["player_id"])

    # Add HC and XP fields to player stats
    op.add_column("player_stats", sa.Column("hc", sa.Integer))
    op.add_column("player_stats", sa.Column("xp", sa.Integer))

    # Make MMR player stat nullable
    op.alter_column("player_stats", "mmr", nullable=True)

    # Null all default MMR players
    player_stats = sa.sql.table("player_stats",
        sa.Column("mmr", sa.Float, nullable=True)
    )
    op.execute(
        player_stats.update().where(player_stats.c.mmr.in_((0.0, 1250.0, 1500.0))).values({"mmr": None})
    )

    # Add indexes for player stats
    op.create_index(op.f("ix_player_stats_mmr"), "player_stats", ["mmr"])
    op.create_index(op.f("ix_player_stats_pilot_level"), "player_stats", ["pilot_level"])
    op.create_index(op.f("ix_player_stats_time_played"), "player_stats", ["time_played"])
    op.create_index(op.f("ix_player_stats_xp"), "player_stats", ["xp"])
    op.create_index(op.f("ix_player_stats_xp_per_min"), "player_stats", ["xp_per_min"])
    op.create_index(op.f("ix_player_stats_hc"), "player_stats", ["hc"])
    op.create_index(op.f("ix_player_stats_hc_per_min"), "player_stats", ["hc_per_min"])
    op.create_index(op.f("ix_player_stats_kda"), "player_stats", ["kda"])
    op.create_index(op.f("ix_player_stats_kill_steals"), "player_stats", ["kill_steals"])
    op.create_index(op.f("ix_player_stats_critical_assists"), "player_stats", ["critical_assists"])
    op.create_index(op.f("ix_player_stats_damage"), "player_stats", ["damage"])
    op.create_index(op.f("ix_player_stats_win_loss"), "player_stats", ["win_loss"])
    op.create_index(op.f("ix_player_stats_dm_win_loss"), "player_stats", ["dm_win_loss"])
    op.create_index(op.f("ix_player_stats_tdm_win_loss"), "player_stats", ["tdm_win_loss"])
    op.create_index(op.f("ix_player_stats_ma_win_loss"), "player_stats", ["ma_win_loss"])
    op.create_index(op.f("ix_player_stats_sg_win_loss"), "player_stats", ["sg_win_loss"])
    op.create_index(op.f("ix_player_stats_coop_win_loss"), "player_stats", ["coop_win_loss"])
    op.create_index(op.f("ix_player_stats_cooptdm_win_loss"), "player_stats", ["cooptdm_win_loss"])

    # Remove old player privacy settings
    op.drop_column("players", "match_privacy")
    op.drop_column("players", "rank_privacy")
    op.drop_column("players", "stats_privacy")

    # Add new player privacy settings
    op.add_column("players", sa.Column("blacklist_by", sa.Integer))
    op.add_column("players", sa.Column("blacklist_reason", sa.String))
    op.add_column("players", sa.Column("blacklisted", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("players", sa.Column("group_privacy", sa.Integer))
    op.add_column("players", sa.Column("link_privacy", sa.Integer))
    op.add_column("players", sa.Column("link_status", sa.Integer, nullable=False, server_default="0"))
    op.add_column("players", sa.Column("link_user", sa.Integer))
    op.create_index(op.f("ix_players_link_user"), "players", ["link_user"])
    op.add_column("players", sa.Column("match_list_privacy", sa.Integer))
    op.add_column("players", sa.Column("match_view_privacy", sa.Integer))
    op.add_column("players", sa.Column("mech_stats_privacy", sa.Integer))
    op.add_column("players", sa.Column("overall_stats_privacy", sa.Integer))
    op.add_column("players", sa.Column("ranked_stats_privacy", sa.Integer))
    op.add_column("players", sa.Column("ranking_privacy", sa.Integer))
    op.add_column("players", sa.Column("region_privacy", sa.Integer))
    op.add_column("players", sa.Column("view_privacy", sa.Integer))

    # Remove server defaults for player privacy settings (default is to populate the fields initially)
    op.alter_column("players", "blacklisted", server_default=None)
    op.alter_column("players", "link_status", server_default=None)

    # Remove old user fields
    op.drop_column("users", "email_confirm_expires")
    op.drop_column("users", "email_confirm_token")
    op.drop_column("users", "associated_player")

    # Add new user fields
    op.add_column("users", sa.Column("password_reset_token", sa.String))
    op.add_column("users", sa.Column("view_privacy", sa.Integer))
    op.add_column("users", sa.Column("link_privacy", sa.Integer))

    # Rename role field
    op.alter_column("users", "type", new_column_name="role_id")

    # Make user emails unique
    op.create_unique_constraint("users_email_key", "users", ["email"])

    # Add indexes for success to the polls and updates tables
    op.create_index(op.f("ix_polls_success"), "polls", ["success"])
    op.create_index(op.f("ix_updates_success"), "updates", ["success"])


def downgrade():
    # Remove indexes for success from the polls and updates tables
    op.drop_index("ix_polls_success", "polls")
    op.drop_index("ix_updates_success", "updates")

    # Remove unique constraint on user emails
    op.drop_constraint("users_email_key", "users")

    # Revert role field to type
    op.alter_column("users", "role_id", new_column_name="type")

    # Remove new user fields
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "view_privacy")
    op.drop_column("users", "link_privacy")

    # Add old user fields
    op.add_column("users", sa.Column("email_confirm_expires", sa.DateTime))
    op.add_column("users", sa.Column("email_confirm_token", sa.String))
    op.add_column("users", sa.Column("associated_player", sa.String(36), sa.ForeignKey("players.id")))

    # Remove new player privacy settings
    op.drop_column("players", "blacklist_by")
    op.drop_column("players", "blacklist_reason")
    op.drop_column("players", "blacklisted")
    op.drop_column("players", "group_privacy")
    op.drop_column("players", "link_privacy")
    op.drop_column("players", "link_status")
    op.drop_column("players", "link_user")
    op.drop_column("players", "match_list_privacy")
    op.drop_column("players", "match_view_privacy")
    op.drop_column("players", "mech_stats_privacy")
    op.drop_column("players", "overall_stats_privacy")
    op.drop_column("players", "ranked_stats_privacy")
    op.drop_column("players", "ranking_privacy")
    op.drop_column("players", "region_privacy")
    op.drop_column("players", "view_privacy")

    # Add old player privacy settings
    op.add_column("players", sa.Column("match_privacy", sa.Integer))
    op.add_column("players", sa.Column("rank_privacy", sa.Integer))
    op.add_column("players", sa.Column("stats_privacy", sa.Integer))

    # Remove indexes for player stats
    op.drop_index("ix_player_stats_mmr", "player_stats")
    op.drop_index("ix_player_stats_pilot_level", "player_stats")
    op.drop_index("ix_player_stats_time_played", "player_stats")
    op.drop_index("ix_player_stats_xp_per_min", "player_stats")
    op.drop_index("ix_player_stats_hc_per_min", "player_stats")
    op.drop_index("ix_player_stats_kda", "player_stats")
    op.drop_index("ix_player_stats_kill_steals", "player_stats")
    op.drop_index("ix_player_stats_critical_assists", "player_stats")
    op.drop_index("ix_player_stats_damage", "player_stats")
    op.drop_index("ix_player_stats_win_loss", "player_stats")
    op.drop_index("ix_player_stats_dm_win_loss", "player_stats")
    op.drop_index("ix_player_stats_tdm_win_loss", "player_stats")
    op.drop_index("ix_player_stats_ma_win_loss", "player_stats")
    op.drop_index("ix_player_stats_sg_win_loss", "player_stats")
    op.drop_index("ix_player_stats_coop_win_loss", "player_stats")
    op.drop_index("ix_player_stats_cooptdm_win_loss", "player_stats")

    # Remove null values for mmr
    player_stats = sa.sql.table("player_stats",
        sa.Column("mmr", sa.Float, nullable=True)
    )
    op.execute(
        player_stats.update().where(player_stats.c.mmr == None).values({"mmr": 0.0})
    )

    # Make MMR player stat not nullable
    op.alter_column("player_stats", "mmr", nullable=False)

    # Remove HC and XP fields from player stats
    op.drop_column("player_stats", "hc")
    op.drop_column("player_stats", "xp")

    # Remove indexes for match players
    op.drop_index("ix_match_players_match_id", "match_players")
    op.drop_index("ix_match_players_player_id", "match_players")

    # Rename tables
    op.rename_table("match_players", "matchplayers")
    op.rename_table("player_stats", "playerstats")

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
