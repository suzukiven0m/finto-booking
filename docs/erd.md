# ERD — schema v1

Schema generato da `backend/app/models.py` e applicato da Alembic
(`0001` → `0002` → `0003`). Sorgente delle decisioni: ADR 0001, ADR 0002,
ADR 0003. Dizionario dei campi: `docs/data-dictionary.md`.

```mermaid
erDiagram
    properties ||--o{ bookings : "property_id"
    properties ||--o{ reviews : "property_id"
    properties ||--o{ guest_requests : "property_id"
    properties ||--o{ kpi_daily : "property_id"

    properties {
        int id PK
        varchar name UK "Buby Lago / Buby Montagna"
        varchar hotel_type "Resort Hotel / City Hotel"
        varchar location_type "lake / mountain"
        int room_count "capacita assunta, non misurata"
        bigint ta_hotel_id UK "hotel TripAdvisor, scelto da DA-2"
    }

    bookings {
        int id PK
        int property_id FK
        date arrival_date
        int lead_time
        int stays_in_weekend_nights
        int stays_in_week_nights
        int nights "GENERATED: weekend + week"
        int adults
        int children
        int babies
        varchar country
        varchar customer_type
        boolean is_repeated_guest
        int previous_cancellations
        int previous_bookings_not_canceled
        varchar market_segment
        varchar distribution_channel
        int agent "id OTA non mappato"
        int company "id azienda non mappato"
        varchar meal
        varchar reserved_room_type
        varchar assigned_room_type
        varchar deposit_type
        int booking_changes
        int days_in_waiting_list
        int required_car_parking_spaces
        int total_of_special_requests
        numeric adr "8,2"
        boolean is_canceled
        date reservation_status_date
    }

    reviews {
        int id PK
        int property_id FK
        bigint ta_hotel_id "denormalizzato dal corpus"
        date post_date
        int stay_year "solo anno: niente trend mensile"
        numeric overall "3,1"
        numeric cleanliness "3,1"
        numeric value "3,1"
        numeric location "3,1"
        numeric rooms "3,1"
        numeric sleep_quality "3,1"
        text title
        text body
        varchar lang
    }

    guest_requests {
        int id PK
        int property_id FK
        timestamptz received_at
        text body
        varchar category "6 categorie"
        text draft_reply
        varchar status "new / draft / sent"
    }

    kpi_daily {
        int id PK
        int property_id FK
        date date
        int room_nights
        numeric revenue "10,2"
        numeric occupancy "5,2 — rapporto 0-1"
        numeric adr "8,2, vuoto se 0 ospiti"
        numeric revenue_per_available_room "8,2"
    }
```

## Vincoli che l'ERD non mostra

| Tabella | Vincolo | Perché |
|---|---|---|
| `properties` | `UNIQUE (ta_hotel_id)` | un hotel TripAdvisor non può essere mappato su due strutture |
| `properties` | `CHECK location_type IN ('lake','mountain')` | due soli valori ammessi dal brief |
| `bookings` | indice `(property_id, arrival_date)` | ogni KPI filtra per hotel e periodo |
| `reviews` | indice `(property_id, post_date)` | trend mensile della dashboard reputazione |
| `guest_requests` | indice `(property_id)` + `CHECK status IN ('new','draft','sent')` | Postgres non indicizza le FK da solo |
| `kpi_daily` | `UNIQUE (property_id, date)` | una sola riga per hotel e giorno |

**Nessuna FK verso `bookings` da `reviews`.** ADR 0003 §3: il legame è per
proprietà, asserito, non per prenotazione. Il `CHECK` di `kpi_daily` è
`UNIQUE`, non `CHECK`: la riga sopra è l'unica eccezione di nomenclatura.
