# se cambi qualcosa qui ricordati di fare una nuova migrazione con alembic
from sqlalchemy import (
    ARRAY,
    Boolean,
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

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    # e' il valore della colonna hotel del csv (Resort Hotel / City Hotel),
    # serve per collegare le prenotazioni all'hotel giusto
    hotel_type = Column(String(50), nullable=False, unique=True)
    location_type = Column(String(20), nullable=False)  # lake o mountain
    # nel csv le camere non ci sono, 190 e 230 li abbiamo ipotizzati noi
    room_count = Column(Integer, nullable=False)


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
    nights = Column(Integer, Computed("stays_in_weekend_nights + stays_in_week_nights", persisted=True))

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
    # recensioni generate (non ci sono nel csv)
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"))

    date = Column(Date, nullable=False)
    score = Column(Numeric(4, 2), nullable=False)  # voto 1-10
    text = Column(Text, nullable=False)
    language = Column(String(5), nullable=False)  # it, en, ...
    reviewer_nationality = Column(String(3))  # tipo ITA, PRT come country

    # queste le riempie il modello di sentiment, all'inizio sono vuote
    sentiment = Column(String(10))  # positive, neutral, negative
    topics = Column(ARRAY(Text))


class GuestRequest(Base):
    # email degli ospiti (generate), per la pagina messaggi
    __tablename__ = "guest_requests"

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
    # room_nights / room_count * 100 (da sentire con Daniele se va in % o 0-1)
    occupancy = Column(Numeric(5, 2), nullable=False)
    # revenue / room_nights, vuoto se quel giorno non c'era nessuno
    adr = Column(Numeric(8, 2))
    # revpar = revenue / room_count
    revenue_per_available_room = Column(Numeric(8, 2), nullable=False)
