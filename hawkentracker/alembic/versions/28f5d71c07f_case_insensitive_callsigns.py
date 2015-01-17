"""Case-insensitive callsigns

Revision ID: 28f5d71c07f
Revises: 4573ad42e11
Create Date: 2015-01-05 14:09:32.827122

"""

# revision identifiers, used by Alembic.
revision = "28f5d71c07f"
down_revision = "4573ad42e11"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Replace players callsign unique constraint with case insensitive index
    op.drop_constraint("players_callsign_key", "players", type_="unique")
    op.create_index("ix_players_callsign", "players", [sa.text("lower(callsign)")], unique=True)


def downgrade():
    # Replace players callsign case insensitive index with unique constraint
    op.drop_index("ix_players_callsign", table_name="players")
    op.create_unique_constraint("players_callsign_key", "players", ["callsign"])
