# Architecture

## Backend: feature-based modules, not layers

```
backend/app/
├── auth/        models.py, schemas.py, service.py, routes.py
├── search/      schemas.py, service.py, routes.py
├── booking/     models.py, schemas.py, service.py, routes.py, exceptions.py
├── payment/     models.py, schemas.py, service.py, factory.py, gateway.py, gateways/
├── operators/   models.py   (Operator, Vehicle, Route, Schedule, Seat)
└── common/      enums.py, security.py, datetime_utils.py, dependencies.py, email.py
```

Each feature module owns its models, schemas, business logic, and routes
together, rather than splitting by technical layer (`models/`, `services/`,
`routes/` as top-level siblings). For a solo developer, this means
everything relevant to "how does booking work" lives in one folder, not
scattered across three. The trade-off: `app/models_registry.py` exists
solely to import every model once so Alembic's autogenerate can discover
them all — a small tax paid once for the navigability benefit.

`app/common/` holds genuinely cross-cutting concerns only: enums (shared
by multiple modules' models), password/token hashing, the
naive-vs-aware datetime fix (see `decisions.md`), and the
`get_current_user` / `require_role` FastAPI dependencies.

## Request flow

```
Route handler (routes.py)
  -> validates request shape via Pydantic schema (schemas.py)
  -> calls service function (service.py), passing the DB session
  -> service function contains ALL business logic and raises
     domain exceptions or HTTPException on failure
  -> route handler returns the service's result, FastAPI serializes
     it via the response_model schema
```

Route handlers are intentionally thin — they exist to translate HTTP
concerns (status codes, request parsing) into service calls. This makes
service functions independently testable without spinning up FastAPI
(see `tests/unit/`), and reusable if a second entry point (a CLI, a
background worker) is ever needed.

## The seat-locking design (most important part of this system)

See `docs/decisions.md` for the full write-up, including the exact
concurrency test results. Summary: seats are individual rows (not a
counter), locked via a conditional `UPDATE ... WHERE status = 'AVAILABLE'`
per seat inside the booking's transaction. This gives atomic
"first request wins" semantics natively from Postgres's row-level MVCC,
with no explicit application-level locking.

## Database schema

11 tables, native Postgres enums for every status field (not free-text
strings) — see `backend/alembic/versions/0001_initial_schema.py` for the
full DDL and the model files under `backend/app/*/models.py` for the ORM
layer.

Key relationships:

```
User 1---1 Operator (an operator account is a user with role=OPERATOR
                      plus an Operator profile row)
Operator 1---N Vehicle
Operator 1---N Route
Route    1---N Schedule
Vehicle  1---N Schedule
Schedule 1---N Seat
User     1---N Booking
Schedule 1---N Booking
Booking  1---N BookingPassenger  (one row per seat in the booking)
Booking  1---1 Payment
```

`Seat.locked_by_booking_id` is a nullable FK back to `Booking` — this is
what the conditional UPDATE sets atomically alongside the status change,
so a locked seat always traces back to exactly one booking.

## Frontend: App Router + feature-adjacent organization

```
frontend/src/
├── app/                          # Next.js App Router pages (route = folder)
│   ├── page.tsx                  # search (home page)
│   ├── login/, register/
│   ├── schedules/[scheduleId]/{seats,passengers,payment}/page.tsx
│   ├── bookings/, bookings/[bookingId]/confirmation/
│   └── profile/
├── components/                   # shared UI: TextField, Button, Alert,
│                                  # SeatMap, TransportBadge, NavBar
├── store/                        # Zustand: auth-store, booking-flow-store
├── hooks/                        # SWR-based data-fetching hooks
├── lib/                          # api-client.ts, validation.ts (zod schemas)
└── types/api.ts                  # hand-synced with backend Pydantic schemas
```

**Why SWR:** seat availability is a genuine real-time race against other
users, not a static resource. `useScheduleDetail` polls every 10s while
the seat-selection screen is mounted specifically so a user is unlikely to
attempt booking a seat someone else has just taken — though the backend's
atomic locking is the actual correctness guarantee; the poll is a UX
improvement that reduces how often a user hits the 409 conflict path, not
what prevents double-booking.

**Why two Zustand stores, not one:** `auth-store` persists to
`localStorage` (session should survive a refresh); `booking-flow-store`
deliberately does not (an in-progress seat selection should not survive a
refresh, since seat locks are time-boxed server-side and a stale client
memory of "my selected seats" would be actively misleading after a
refresh — better to make the user reselect against fresh data).

**Why types are hand-synced, not codegen'd:** for a 2-day MVP with one
developer maintaining both ends, setting up `openapi-typescript` or
similar is more setup cost than the type-drift risk it prevents. Revisit
once the API stabilizes or a second developer joins, at which point drift
risk rises sharply and codegen starts paying for itself.
