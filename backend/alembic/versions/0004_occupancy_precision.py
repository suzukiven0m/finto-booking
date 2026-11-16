"""occupancy: numeric(5,2) -> numeric(5,4)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # occupazione e' un rapporto 0-1: con 2 decimali si quantizza a 1 punto
    # percentuale (una camera al Buby Lago vale 0,53%) e le medie derivate
    # derivano. 4 decimali sono gratis e tolgono il problema (playbook §4.3).
    op.alter_column(
        "kpi_daily",
        "occupancy",
        type_=sa.Numeric(5, 4),
        existing_type=sa.Numeric(5, 2),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "kpi_daily",
        "occupancy",
        type_=sa.Numeric(5, 2),
        existing_type=sa.Numeric(5, 4),
        existing_nullable=False,
    )
