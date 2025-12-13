"""seed mock data

Revision ID: 97e0424909f9
Revises: 7c771bba3ad7
Create Date: 2025-09-23 15:10:54.535305

"""

from typing import Sequence, Union
import uuid
import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "97e0424909f9"
down_revision: Union[str, Sequence[str], None] = "7c771bba3ad7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Populate database with mock data."""
    users_table = sa.table(
        "users",
        sa.column("id", sa.UUID),
        sa.column("name", sa.String),
        sa.column("email", sa.String),
        sa.column("is_verified_author", sa.Boolean),
        sa.column("registered_at", sa.DateTime(timezone=True)),
    )
    news_table = sa.table(
        "news",
        sa.column("id", sa.UUID),
        sa.column("title", sa.String),
        sa.column("content", sa.JSON),
        sa.column("author_id", sa.UUID),
        sa.column("published_at", sa.DateTime(timezone=True)),
    )

    verified_author_id = uuid.uuid4()
    regular_user_id = uuid.uuid4()
    news_id = uuid.uuid4()

    op.bulk_insert(
        users_table,
        [
            {
                "id": verified_author_id,
                "name": "Verified Author",
                "email": "author@example.com",
                "is_verified_author": True,
                "registered_at": datetime.datetime.now(datetime.timezone.utc),
            },
            {
                "id": regular_user_id,
                "name": "Regular User",
                "email": "user@example.com",
                "is_verified_author": False,
                "registered_at": datetime.datetime.now(datetime.timezone.utc),
            },
        ],
    )

    op.bulk_insert(
        news_table,
        [
            {
                "id": news_id,
                "title": "FastAPI is Awesome!",
                "content": {"text": "Here is a detailed article about FastAPI."},
                "author_id": verified_author_id,
                "published_at": datetime.datetime.now(datetime.timezone.utc),
            }
        ],
    )


def downgrade() -> None:
    """Clean up mock data."""
    op.execute("DELETE FROM news")
    op.execute("DELETE FROM users")
