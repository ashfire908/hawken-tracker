"""Remove users and permissions

Revision ID: 593f1ba4670
Revises: 46d439ae26a
Create Date: 2015-11-14 15:42:03.438148

"""

# revision identifiers, used by Alembic.
revision = "593f1ba4670"
down_revision = "46d439ae26a"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Remove player linking
    op.drop_index("ix_players_link_user", table_name="players")
    op.drop_constraint("players_link_user_fkey", "players", type_="foreignkey")
    op.drop_column("players", "link_user")
    op.drop_column("players", "link_status")

    # Remove player blacklist by field
    op.drop_constraint("players_blacklist_by_fkey", "players", type_="foreignkey")
    op.drop_column("players", "blacklist_by")

    # Remove player privacy settings
    op.drop_column("players", "home_region")
    op.drop_column("players", "group_privacy")
    op.drop_column("players", "leaderboard_privacy")
    op.drop_column("players", "link_privacy")
    op.drop_column("players", "match_list_privacy")
    op.drop_column("players", "match_view_privacy")
    op.drop_column("players", "mech_stats_privacy")
    op.drop_column("players", "overall_stats_privacy")
    op.drop_column("players", "ranked_stats_privacy")
    op.drop_column("players", "ranking_privacy")
    op.drop_column("players", "region_privacy")
    op.drop_column("players", "view_privacy")

    # Drop user and permission tables
    op.drop_table("users")
    op.drop_table("user_permissions")
    op.drop_table("user_roles")


def downgrade():
    # Create user roles table
    op.create_table("user_roles",
        sa.Column("role_id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("name", sa.String, unique=True, nullable=False),
        sa.Column("superadmin", sa.Boolean, nullable=False)
    )

    # Create user permissions table
    op.create_table("user_permissions",
        sa.Column("role_id", sa.Integer, sa.ForeignKey("user_roles.role_id"), primary_key=True, index=True),
        sa.Column("permission", sa.String, primary_key=True),
        sa.Column("power", sa.Integer)
    )

    # Create users table
    op.create_table("users",
        sa.Column("user_id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("username", sa.String, nullable=False),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("password", sa.String, nullable=False),
        sa.Column("creation", sa.DateTime, nullable=False),
        sa.Column("locked", sa.Boolean, nullable=False),
        sa.Column("lock_reason", sa.String),
        sa.Column("lock_by", sa.Integer, sa.ForeignKey("users.user_id")),
        sa.Column("confirmed", sa.Boolean, nullable=False),
        sa.Column("confirmed_at", sa.DateTime),
        sa.Column("email_confirmation_for", sa.String),
        sa.Column("email_confirmation_token", sa.String),
        sa.Column("email_confirmation_sent_at", sa.DateTime),
        sa.Column("password_reset_token", sa.String),
        sa.Column("password_reset_sent_at", sa.DateTime),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("user_roles.role_id"), nullable=False),
        sa.Column("view_privacy", sa.Integer),
        sa.Column("link_privacy", sa.Integer)
    )

    # Create user unique constraints
    op.create_index("ix_users_username", "users", [sa.text("lower(username)")], unique=True)
    op.create_index("ix_users_email", "users", [sa.text("lower(email)")], unique=True)
    op.create_index("ix_users_email_confirmation_for", "users", [sa.text("lower(email_confirmation_for)")], unique=True)

    # Add player privacy settings
    op.add_column("players", sa.Column("view_privacy", sa.Integer))
    op.add_column("players", sa.Column("region_privacy", sa.Integer))
    op.add_column("players", sa.Column("ranking_privacy", sa.Integer))
    op.add_column("players", sa.Column("ranked_stats_privacy", sa.Integer))
    op.add_column("players", sa.Column("overall_stats_privacy", sa.Integer))
    op.add_column("players", sa.Column("mech_stats_privacy", sa.Integer))
    op.add_column("players", sa.Column("match_view_privacy", sa.Integer))
    op.add_column("players", sa.Column("match_list_privacy", sa.Integer))
    op.add_column("players", sa.Column("link_privacy", sa.Integer))
    op.add_column("players", sa.Column("leaderboard_privacy", sa.Integer))
    op.add_column("players", sa.Column("group_privacy", sa.Integer))
    op.add_column("players", sa.Column("home_region", sa.Integer))

    # Add player blacklist by field
    op.add_column("players", sa.Column("blacklist_by", sa.Integer, sa.ForeignKey("users.user_id")))

    # Add player linking
    op.add_column("players", sa.Column("link_status", sa.Integer, nullable=False, server_default="0"))
    op.add_column("players", sa.Column("link_user", sa.Integer, sa.ForeignKey("users.user_id"), index=True))

    # Remove server defaults for player link status (default is to populate the field initially)
    op.alter_column("players", "link_status", server_default=None)
