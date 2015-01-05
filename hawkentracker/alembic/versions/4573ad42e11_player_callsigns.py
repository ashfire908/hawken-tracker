"""Player callsigns

Revision ID: 4573ad42e11
Revises: 29bd54773b6
Create Date: 2015-01-04 22:35:50.409172

"""

# revision identifiers, used by Alembic.
revision = "4573ad42e11"
down_revision = "29bd54773b6"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add player callsign column
    op.add_column("players", sa.Column("callsign", sa.String, unique=True))


def downgrade():
    # Remove player callsign column
    op.drop_column("players", "callsign")
