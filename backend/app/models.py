# se cambi qualcosa qui ricordati di fare una nuova migrazione con alembic
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("ta_hotel_id", name="uq_properties_ta_hotel_id"),
        CheckConstraint(
            "location_type IN ('lake', 'mountain')", name="ck_properties_location_type"
        ),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    # e' il valore della colonna hotel del csv (Resort Hotel / City Hotel),
    # serve per collegare le prenotazioni all'hotel giusto.
    # Non e' unique: due strutture possono essere entrambe "City Hotel".
    hotel_type = Column(String(50), nullable=False)
    location_type = Column(String(20), nullable=False)  # lake o mountain
    # nel csv le camere non ci sono, 190 e 230 li abbiamo ipotizzati noi
    room_count = Column(Integer, nullable=False)
    # hotel TripAdvisor scelto per questa struttura (ADR 0003 §1): quello con
    # piu' recensioni. Si sceglie una volta e non si cambia dopo il SAL 1.
    ta_hotel_id = Column(BigInteger)


class Booking(Base):
    # una riga del csv hotel_bookings, i nomi delle colonne sono quasi tutti uguali
    __tablename__ = "bookings"
    __table_args__ = (Index("ix_bookings_property_arrival", "property_id", "arrival_date"),)

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # anno, mese e giorno del csv messi insieme in una data sola
    # week_number e reservation_status non li salvo perche si ricavano
    arrival_date = Column(Date, nullable=False)
    lead_time = Column(Integer, nullable=False)
    stays_in_weekend_nights = Column(Integer, nullable=False)
    stays_in_week_nights = Column(Integer, nullable=False)
    # la calcola postgres da solo, non va scritta quando si caricano i dati
    nights = Column(
        Integer, Computed("stays_in_weekend_nights + stays_in_week_nights", persisted=True)
    )

    adults = Column(Integer, nullable=False)
    children = Column(Integer, nullable=False, server_default="0")  # nel csv ci sono 4 NA
    babies = Column(Integer, nullable=False, server_default="0")
    country = Column(String(3))
    customer_type = Column(String(30), nullable=False)
    is_repeated_guest = Column(Boolean, nullable=False)
    previous_cancellations = Column(Integer, nullable=False)
    previous_bookings_not_canceled = Column(Integer, nullable=False)

    market_segment = Column(String(30), nullable=False)
    distribution_channel = Column(String(30), nullable=False)
    agent = Column(Integer)  # nel csv c'e scritto "NULL", va messo vuoto
    company = Column(Integer)  # idem

    meal = Column(String(20), nullable=False)
    reserved_room_type = Column(String(5), nullable=False)
    assigned_room_type = Column(String(5), nullable=False)
    deposit_type = Column(String(20), nullable=False)
    booking_changes = Column(Integer, nullable=False)
    days_in_waiting_list = Column(Integer, nullable=False)
    required_car_parking_spaces = Column(Integer, nullable=False)
    total_of_special_requests = Column(Integer, nullable=False)

    adr = Column(Numeric(8, 2), nullable=False)
    is_canceled = Column(Boolean, nullable=False)
    reservation_status_date = Column(Date, nullable=False)


class Review(Base):
    # recensioni dal corpus TripAdvisor (ADR 0003 §3, opzione E).
    # Nessuna FK verso bookings: il legame e' a livello di proprieta', asserito.
    __tablename__ = "reviews"
    __table_args__ = (Index("ix_reviews_property_post_date", "property_id", "post_date"),)

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    # denormalizzato apposta: traccia da quale hotel TripAdvisor arriva la riga
    ta_hotel_id = Column(BigInteger, nullable=False)

    post_date = Column(Date, nullable=False)  # da post_date, non da stay_year
    stay_year = Column(Integer)  # solo l'anno: non basta per il trend mensile

    # voti 1-5 con un decimale, presi dal corpus
    overall = Column(Numeric(3, 1))
    cleanliness = Column(Numeric(3, 1))
    value = Column(Numeric(3, 1))
    location = Column(Numeric(3, 1))
    rooms = Column(Numeric(3, 1))
    sleep_quality = Column(Numeric(3, 1))

    title = Column(Text)
    body = Column(Text)
    lang = Column(String(20))

    # sentiment e topics NON stanno qui: sono output del modello (D14), non dati
    # di TripAdvisor. Vanno in una tabella derivata, cosi' un re-run del modello
    # non deve fare UPDATE sulla tabella sorgente.


class GuestRequest(Base):
    # email degli ospiti (generate), per la pagina messaggi
    __tablename__ = "guest_requests"
    __table_args__ = (
        Index("ix_guest_requests_property_id", "property_id"),
        CheckConstraint("status IN ('new', 'draft', 'sent')", name="ck_guest_requests_status"),
    )

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    received_at = Column(DateTime(timezone=True), nullable=False)
    body = Column(Text, nullable=False)

    # categoria e bozza le mette l'assistente
    category = Column(String(50))
    draft_reply = Column(Text)
    status = Column(String(20), nullable=False, server_default="new")  # new, draft, sent


class KpiDaily(Base):
    # kpi per hotel e per giorno, calcolati dalle prenotazioni non cancellate
    __tablename__ = "kpi_daily"
    __table_args__ = (UniqueConstraint("property_id", "date", name="uq_kpi_daily_property_date"),)

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    date = Column(Date, nullable=False)

    room_nights = Column(Integer, nullable=False)
    revenue = Column(Numeric(10, 2), nullable=False)
    # room_nights / room_count: rapporto 0-1, senza x100 (delivery-plan §6)
    occupancy = Column(Numeric(5, 2), nullable=False)
    # revenue / room_nights, vuoto se quel giorno non c'era nessuno
    adr = Column(Numeric(8, 2))
    # revpar = revenue / room_count
    revenue_per_available_room = Column(Numeric(8, 2), nullable=False)
