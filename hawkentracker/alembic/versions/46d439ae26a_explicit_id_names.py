"""Explicit id names

Revision ID: 46d439ae26a
Revises: 3cd555b6685
Create Date: 2015-10-26 18:51:12.160056

"""

# revision identifiers, used by Alembic.
revision = "46d439ae26a"
down_revision = "3cd555b6685"

from alembic import op


def upgrade():
    # Rename id columns
    op.alter_column("players", "id", new_column_name="player_id")
    op.alter_column("matches", "id", new_column_name="match_id")
    op.alter_column("users", "id", new_column_name="user_id")
    op.alter_column("user_roles", "id", new_column_name="role_id")


def downgrade():
    # Rename id columns
    op.alter_column("user_roles", "role_id", new_column_name="id")
    op.alter_column("users", "user_id", new_column_name="id")
    op.alter_column("matches", "match_id", new_column_name="id")
    op.alter_column("players", "player_id", new_column_name="id")
