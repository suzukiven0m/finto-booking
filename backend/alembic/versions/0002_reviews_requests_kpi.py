"""Schema v1: reviews, guest_requests, kpi_daily

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-13
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id")),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("score", sa.Numeric(4, 2), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("reviewer_nationality", sa.String(3)),
        sa.Column("sentiment", sa.String(10)),
        sa.Column("topics", sa.ARRAY(sa.Text())),
    )

    op.create_table(
        "guest_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50)),
        sa.Column("draft_reply", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
    )

    op.create_table(
        "kpi_daily",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("room_nights", sa.Integer(), nullable=False),
        sa.Column("revenue", sa.Numeric(10, 2), nullable=False),
        sa.Column("occupancy", sa.Numeric(5, 2), nullable=False),
        sa.Column("adr", sa.Numeric(8, 2)),
        sa.Column("revenue_per_available_room", sa.Numeric(8, 2), nullable=False),
        sa.UniqueConstraint("property_id", "date", name="uq_kpi_daily_property_date"),
    )


def downgrade() -> None:
    op.drop_table("kpi_daily")
    op.drop_table("guest_requests")
    op.drop_table("reviews")
