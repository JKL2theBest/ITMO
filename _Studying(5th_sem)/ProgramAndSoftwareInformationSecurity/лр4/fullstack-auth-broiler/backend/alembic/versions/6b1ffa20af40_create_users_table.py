"""create_users_table

Revision ID: 6b1ffa20af40
Revises:
Create Date: 2025-10-20 10:20:16.200917

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6b1ffa20af40"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("login", sa.String(32), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login"),
    )
    op.create_index(op.f("ix_users_login"), "users", ["login"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_login"), table_name="users")
    op.drop_table("users")
