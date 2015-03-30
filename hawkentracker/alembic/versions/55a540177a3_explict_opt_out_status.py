"""Explict opt out status

Revision ID: 55a540177a3
Revises: 276a9c91812
Create Date: 2015-03-30 13:21:10.374065

"""

# revision identifiers, used by Alembic.
revision = "55a540177a3"
down_revision = "276a9c91812"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Allow for nullable opt out
    op.alter_column("players", "opt_out", nullable=True)

    # Convert false opt out to null
    players = sa.sql.table("players",
        sa.Column("opt_out", sa.Boolean, nullable=True)
    )
    op.execute(
        players.update().where(players.c.opt_out == False).values({"opt_out": None})
    )


def downgrade():
    # Convert null opt out to false
    players = sa.sql.table("players",
        sa.Column("opt_out", sa.Boolean, nullable=True)
    )
    op.execute(
        players.update().where(players.c.opt_out == None).values({"opt_out": False})
    )

    # Disallow for nullable opt out
    op.alter_column("players", "opt_out", nullable=False)
