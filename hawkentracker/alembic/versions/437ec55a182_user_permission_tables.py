"""User permission tables

Revision ID: 437ec55a182
Revises: 150ac16c9a1
Create Date: 2014-08-10 21:19:13.816085

"""

# revision identifiers, used by Alembic.
revision = "437ec55a182"
down_revision = "150ac16c9a1"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Create user roles table
    op.create_table("user_roles",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("name", sa.String, unique=True,nullable=False),
        sa.Column("superadmin", sa.Boolean, nullable=False)
    )

    # Create user permissions table
    op.create_table("user_permissions",
        sa.Column("role_id", sa.Integer, sa.ForeignKey("user_roles.id"), primary_key=True, index=True),
        sa.Column("permission", sa.String, primary_key=True),
        sa.Column("power", sa.Integer)
    )


def downgrade():
    # Drop user role/permission tables
    op.drop_table("user_permissions")
    op.drop_table("user_roles")
