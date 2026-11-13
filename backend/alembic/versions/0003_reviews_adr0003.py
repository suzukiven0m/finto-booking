"""ADR 0003: reviews dalla forma sintetica al corpus TripAdvisor

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-13

ADR 0003 (accettato 2026-11-13, opzione E) sostituisce le recensioni
generate con il corpus TripAdvisor. La tabella `reviews` era stata
congelata in 0002 sulla forma sintetica: qui viene portata alla §3
dell'ADR.

La tabella è vuota (il loader D8 non esiste ancora), ma le rinomine
usano alter_column invece di drop+create, così se qualcuno ha già
caricato qualcosa non lo perde.
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

DIMENSIONS = ("cleanliness", "value", "location", "rooms", "sleep_quality")


def upgrade() -> None:
    # --- properties: ta_hotel_id (ADR 0003 §1) ---
    op.add_column("properties", sa.Column("ta_hotel_id", sa.BigInteger()))
    op.create_unique_constraint("uq_properties_ta_hotel_id", "properties", ["ta_hotel_id"])
    # hotel_type non è una seconda chiave naturale: due hotel possono
    # essere entrambi "City Hotel". Era unique per caso in 0001.
    op.drop_constraint("properties_hotel_type_key", "properties", type_="unique")
    op.create_check_constraint(
        "ck_properties_location_type", "properties", "location_type IN ('lake', 'mountain')"
    )

    # --- reviews: rinomine, i nomi sono quelli del corpus ---
    op.alter_column("reviews", "date", new_column_name="post_date")
    op.alter_column("reviews", "score", new_column_name="overall")
    op.alter_column("reviews", "text", new_column_name="body")
    op.alter_column("reviews", "language", new_column_name="lang")

    # --- reviews: colonne che il corpus non ha ---
    op.drop_column("reviews", "booking_id")
    op.drop_column("reviews", "reviewer_nationality")
    # sentiment e topics sono output del modello (D14), non dati di TripAdvisor
    op.drop_column("reviews", "sentiment")
    op.drop_column("reviews", "topics")

    # --- reviews: colonne del corpus ---
    op.add_column("reviews", sa.Column("ta_hotel_id", sa.BigInteger(), nullable=False))
    op.add_column("reviews", sa.Column("stay_year", sa.Integer()))
    op.add_column("reviews", sa.Column("title", sa.Text()))
    for dim in DIMENSIONS:
        op.add_column("reviews", sa.Column(dim, sa.Numeric(3, 1)))

    # overall è un voto 1-5 con un decimale, non 1-10 con due. Nel corpus
    # puo' essere vuoto (recensione senza voto), quindi via il NOT NULL di 0002.
    op.alter_column(
        "reviews",
        "overall",
        type_=sa.Numeric(3, 1),
        existing_type=sa.Numeric(4, 2),
        nullable=True,
    )
    op.alter_column("reviews", "body", existing_type=sa.Text(), nullable=True)
    op.alter_column(
        "reviews", "lang", type_=sa.String(20), existing_type=sa.String(5), nullable=True
    )

    # il trend mensile della dashboard reputazione filtra per hotel e data
    op.create_index("ix_reviews_property_post_date", "reviews", ["property_id", "post_date"])

    # --- guest_requests: indice sulla FK + vocabolario chiuso ---
    op.create_index("ix_guest_requests_property_id", "guest_requests", ["property_id"])
    op.create_check_constraint(
        "ck_guest_requests_status", "guest_requests", "status IN ('new', 'draft', 'sent')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_guest_requests_status", "guest_requests", type_="check")
    op.drop_index("ix_guest_requests_property_id", table_name="guest_requests")
    op.drop_index("ix_reviews_property_post_date", table_name="reviews")

    op.alter_column(
        "reviews", "lang", type_=sa.String(5), existing_type=sa.String(20), nullable=False
    )
    op.alter_column("reviews", "body", existing_type=sa.Text(), nullable=False)
    op.alter_column(
        "reviews", "overall", type_=sa.Numeric(4, 2), existing_type=sa.Numeric(3, 1)
    )

    for dim in reversed(DIMENSIONS):
        op.drop_column("reviews", dim)
    op.drop_column("reviews", "title")
    op.drop_column("reviews", "stay_year")
    op.drop_column("reviews", "ta_hotel_id")

    op.add_column("reviews", sa.Column("topics", sa.ARRAY(sa.Text())))
    op.add_column("reviews", sa.Column("sentiment", sa.String(10)))
    op.add_column("reviews", sa.Column("reviewer_nationality", sa.String(3)))
    op.add_column(
        "reviews", sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id"))
    )

    op.alter_column("reviews", "lang", new_column_name="language")
    op.alter_column("reviews", "body", new_column_name="text")
    op.alter_column("reviews", "overall", new_column_name="score")
    op.alter_column("reviews", "post_date", new_column_name="date")

    op.drop_constraint("ck_properties_location_type", "properties", type_="check")
    op.create_unique_constraint("properties_hotel_type_key", "properties", ["hotel_type"])
    op.drop_constraint("uq_properties_ta_hotel_id", "properties", type_="unique")
    op.drop_column("properties", "ta_hotel_id")
