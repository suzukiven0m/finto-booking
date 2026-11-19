"""guest_requests: urgency varchar(10) nullable + CHECK low/medium/high

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # decisione pre-freeze 2026-11-19 (audit S8): il gold file valuta
    # true_urgency, la colonna dà una casa all'output prima del freeze.
    # Resta NULL finché D15 non la produce, come category/draft_reply.
    op.add_column("guest_requests", sa.Column("urgency", sa.String(10)))
    op.create_check_constraint(
        "ck_guest_requests_urgency", "guest_requests", "urgency IN ('low', 'medium', 'high')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_guest_requests_urgency", "guest_requests", type_="check")
    op.drop_column("guest_requests", "urgency")
