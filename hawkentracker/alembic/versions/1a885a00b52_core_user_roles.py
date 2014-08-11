"""Core user roles

Revision ID: 1a885a00b52
Revises: 437ec55a182
Create Date: 2014-08-10 21:19:22.299570

"""

# revision identifiers, used by Alembic.
revision = "1a885a00b52"
down_revision = "437ec55a182"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Define table
    roles = sa.sql.table("user_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, unique=True, nullable=False),
        sa.Column("superadmin", sa.Boolean, nullable=False)
    )

    # Add core roles
    op.bulk_insert(roles,
        [
            {"id": 1, "name": "Anonymous", "superadmin": False},
            {"id": 2, "name": "Unconfirmed User", "superadmin": False},
            {"id": 3, "name": "Standard User", "superadmin": False}
        ]
    )


def downgrade():
    # Define tables
    roles = sa.sql.table("user_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, unique=True, nullable=False),
        sa.Column("superadmin", sa.Boolean, nullable=False)
    )

    permissions = sa.sql.table("user_permissions",
        sa.Column("role_id", sa.Integer, sa.ForeignKey("user_roles.id"), primary_key=True, index=True),
        sa.Column("permission", sa.String, primary_key=True),
        sa.Column("power", sa.Integer)
    )

    # Remove core role permissions
    op.execute(
        permissions.delete().where(permissions.c.role_id.in_((1, 2, 3)))
    )

    # Remove core roles
    op.execute(
        roles.delete().where(roles.c.id.in_((1, 2, 3)))
    )
