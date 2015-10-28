"""Match start/end event data

Revision ID: 52eed5f8cd4
Revises: 46d439ae26a
Create Date: 2015-10-27 23:08:24.944633

"""

# revision identifiers, used by Alembic.
revision = "52eed5f8cd4"
down_revision = "46d439ae26a"

from alembic import op
import sqlalchemy as sa

DEFAULT_GUID = "00000000-0000-0000-0000-000000000000"


def upgrade():
    # Create match server id field
    op.add_column("matches", sa.Column("server_id", sa.String(36), index=True, nullable=False, server_default=DEFAULT_GUID))

    # Remove server default (default is to populate the fields initially)
    op.alter_column("matches", "server_id", server_default=None)

    # Create match info fields
    op.add_column("matches", sa.Column("match_started", sa.DateTime))
    op.add_column("matches", sa.Column("match_ended", sa.DateTime))
    op.add_column("matches", sa.Column("players_started", sa.Integer))
    op.add_column("matches", sa.Column("players_started_inactive", sa.Integer))
    op.add_column("matches", sa.Column("players_ended", sa.Integer))
    op.add_column("matches", sa.Column("players_ended_inactive", sa.Integer))
    op.add_column("matches", sa.Column("bots_started", sa.Integer))
    op.add_column("matches", sa.Column("bots_ended", sa.Integer))
    op.add_column("matches", sa.Column("winning_team", sa.Integer))
    op.add_column("matches", sa.Column("win_reason", sa.String))

    # Create match player fields
    op.add_column("match_players", sa.Column("match_team", sa.Integer))
    op.add_column("match_players", sa.Column("match_kills", sa.Integer))
    op.add_column("match_players", sa.Column("player_mmr", sa.Float))
    op.add_column("match_players", sa.Column("xp_gained", sa.Integer))
    op.add_column("match_players", sa.Column("hc_gained", sa.Integer))
    op.add_column("match_players", sa.Column("started_with", sa.Boolean))
    op.add_column("match_players", sa.Column("ended_with", sa.Boolean))


def downgrade():
    # Drop match player fields
    op.drop_column("match_players", "ended_with")
    op.drop_column("match_players", "started_with")
    op.drop_column("match_players", "hc_gained")
    op.drop_column("match_players", "xp_gained")
    op.drop_column("match_players", "player_mmr")
    op.drop_column("match_players", "match_kills")
    op.drop_column("match_players", "match_team")

    # Remove match info fields
    op.drop_column("matches", "win_reason")
    op.drop_column("matches", "winning_team")
    op.drop_column("matches", "bots_ended")
    op.drop_column("matches", "bots_started")
    op.drop_column("matches", "players_ended_inactive")
    op.drop_column("matches", "players_ended")
    op.drop_column("matches", "players_started_inactive")
    op.drop_column("matches", "players_started")
    op.drop_column("matches", "match_ended")
    op.drop_column("matches", "match_started")

    # Remove match server id field
    op.drop_column("matches", "server_id")
