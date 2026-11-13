"""Schema v1: properties e bookings

Revision ID: 0001
Revises:
Create Date: 2026-11-12
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    properties = op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("hotel_type", sa.String(50), nullable=False, unique=True),
        sa.Column("location_type", sa.String(20), nullable=False),
        sa.Column("room_count", sa.Integer(), nullable=False),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("arrival_date", sa.Date(), nullable=False),
        sa.Column("lead_time", sa.Integer(), nullable=False),
        sa.Column("stays_in_weekend_nights", sa.Integer(), nullable=False),
        sa.Column("stays_in_week_nights", sa.Integer(), nullable=False),
        sa.Column(
            "nights",
            sa.Integer(),
            sa.Computed("stays_in_weekend_nights + stays_in_week_nights", persisted=True),
        ),
        sa.Column("adults", sa.Integer(), nullable=False),
        sa.Column("children", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("babies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("country", sa.String(3)),
        sa.Column("customer_type", sa.String(30), nullable=False),
        sa.Column("is_repeated_guest", sa.Boolean(), nullable=False),
        sa.Column("previous_cancellations", sa.Integer(), nullable=False),
        sa.Column("previous_bookings_not_canceled", sa.Integer(), nullable=False),
        sa.Column("market_segment", sa.String(30), nullable=False),
        sa.Column("distribution_channel", sa.String(30), nullable=False),
        sa.Column("agent", sa.Integer()),
        sa.Column("company", sa.Integer()),
        sa.Column("meal", sa.String(20), nullable=False),
        sa.Column("reserved_room_type", sa.String(5), nullable=False),
        sa.Column("assigned_room_type", sa.String(5), nullable=False),
        sa.Column("deposit_type", sa.String(20), nullable=False),
        sa.Column("booking_changes", sa.Integer(), nullable=False),
        sa.Column("days_in_waiting_list", sa.Integer(), nullable=False),
        sa.Column("required_car_parking_spaces", sa.Integer(), nullable=False),
        sa.Column("total_of_special_requests", sa.Integer(), nullable=False),
        sa.Column("adr", sa.Numeric(8, 2), nullable=False),
        sa.Column("is_canceled", sa.Boolean(), nullable=False),
        sa.Column("reservation_status_date", sa.Date(), nullable=False),
    )
    # indice per cercare per hotel e data (lo usano i kpi)
    op.create_index("ix_bookings_property_arrival", "bookings", ["property_id", "arrival_date"])

    # i due hotel (id 1 e 2 li mette postgres), le camere sono ipotizzate
    op.bulk_insert(
        properties,
        [
            {
                "name": "Buby Lago",
                "hotel_type": "Resort Hotel",
                "location_type": "lake",
                "room_count": 190,
            },
            {
                "name": "Buby Montagna",
                "hotel_type": "City Hotel",
                "location_type": "mountain",
                "room_count": 230,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_property_arrival", table_name="bookings")
    op.drop_table("bookings")
    op.drop_table("properties")
