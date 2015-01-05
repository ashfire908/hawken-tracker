"""Account revamp

Revision ID: 29bd54773b6
Revises: a8503d5ea8
Create Date: 2014-12-26 23:38:23.554505

"""

# revision identifiers, used by Alembic.
revision = "29bd54773b6"
down_revision = "a8503d5ea8"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add missing player foreign keys
    op.create_foreign_key("players_blacklist_by_fkey", "players", "users", ["blacklist_by"], ["id"])
    op.create_foreign_key("players_link_user_fkey", "players", "users", ["link_user"], ["id"])

    # Add missing user foreign key
    op.create_foreign_key("users_role_id_fkey", "users", "user_roles", ["role_id"], ["id"])

    # Rename email confirmation column
    op.alter_column("users", "email_confirmed", new_column_name="confirmed")

    # Create new email confirmation columns
    op.add_column("users", sa.Column("confirmed_at", sa.DateTime))
    op.add_column("users", sa.Column("email_confirmation_for", sa.String))
    op.add_column("users", sa.Column("email_confirmation_sent_at", sa.DateTime))
    op.add_column("users", sa.Column("email_confirmation_token", sa.String))

    # Create new account lock columns
    op.add_column("users", sa.Column("locked", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("users", sa.Column("lock_by", sa.Integer, sa.ForeignKey("users.id")))
    op.add_column("users", sa.Column("lock_reason", sa.String))

    # Remove server defaults for player privacy settings (default is to populate the fields initially)
    op.alter_column("users", "locked", server_default=None)

    # Add password reset timestamp for reset ttl
    op.add_column("users", sa.Column("password_reset_sent_at", sa.DateTime))

    # Remove unique constraints and replace with unique indexes. Make main and pending emails one index
    op.drop_constraint("users_username_key", "users", type_="unique")
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.create_index("ix_users_username", "users", [sa.text("lower(username)")], unique=True)
    op.create_index("ix_users_email", "users", [sa.text("lower(email)")], unique=True)
    op.create_index("ix_users_email_confirmation_for", "users", [sa.text("lower(email_confirmation_for)")], unique=True)


def downgrade():
    # Recreate original unique constraints
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_email_confirmation_for", table_name="users")
    op.create_unique_constraint("users_username_key", "users", ["username"])
    op.create_unique_constraint("users_email_key", "users", ["email"])

    # Remove user foreign keys
    op.drop_constraint("users_role_id_fkey", "users", type_="foreignkey")
    op.drop_constraint("users_lock_by_fkey", "users", type_="foreignkey")

    # Remove password reset timestamp
    op.drop_column("users", "password_reset_sent_at")

    # Remove new account lock columns
    op.drop_column("users", "locked")
    op.drop_column("users", "lock_reason")
    op.drop_column("users", "lock_by")

    # Remove new email confirmation columns
    op.drop_column("users", "confirmed_at")
    op.drop_column("users", "email_confirmation_for")
    op.drop_column("users", "email_confirmation_sent_at")
    op.drop_column("users", "email_confirmation_token")

    # Rename email confirmation column
    op.alter_column("users", "confirmed", new_column_name="email_confirmed")

    # Remove player foreign keys
    op.drop_constraint("players_blacklist_by_fkey", "players", type_="foreignkey")
    op.drop_constraint("players_link_user_fkey", "players", type_="foreignkey")
