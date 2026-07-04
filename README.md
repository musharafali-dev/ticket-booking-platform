# Ticket Booking Platform — Pakistan

A ticket booking MVP for buses, trains, and airplanes across Pakistan.
FastAPI + PostgreSQL backend, Next.js 14 frontend, JWT auth, and a
gateway-agnostic payment abstraction ready for JazzCash/EasyPaisa.

**Status:** Core booking flow (search → seat selection → passenger
details → payment → confirmation) is implemented, tested, and verified
against a real PostgreSQL database. See [`docs/decisions.md`](docs/decisions.md)
for what was found and fixed along the way, and the **Known Limitations**
section below for what is honestly not yet done.

---

## What's actually here

| Area | Status |
|---|---|
| Auth (register, email verification, login, JWT + refresh rotation, RBAC) | Implemented, tested |
| Search (route/date/transport-type filtering) | Implemented, tested |
| Booking (seat locking, cancellation, expiry) | Implemented, tested — concurrency-verified against real Postgres |
| Payment (mock gateway + JazzCash/EasyPaisa structurally-correct stubs) | Implemented, tested |
| Frontend core flow (search to seats to passengers to pay to confirm) | Implemented, type-checked, contract-verified against live backend |
| Frontend profile page | Deliberate stub (display-only, no editing) — see decisions.md |
| Operator dashboard, admin panel | Not built (backend models exist; no routes/UI) |
| Real JazzCash/EasyPaisa credentials | Not configured (mock gateway only; stubs are structurally correct and documented) |
| Docker Compose full stack | Config written and structurally validated; `docker compose up` itself not run (no Docker daemon in the dev sandbox — see decisions.md) |
| Browser-driven / E2E UI tests | Not performed (no headless browser tooling in the dev sandbox); contract-level verification via curl was performed instead |

---

## Architecture

```
+----------------------+        +---------------------------+
|   Next.js 14         |  HTTP  |   FastAPI                 |
|   (App Router)        |<------>|   /api/v1/*               |
|   TypeScript, Tailwind|  JSON  |                           |
|   Zustand, SWR         |        |  auth . search . booking  |
+----------------------+        |  . payment                |
                                 +------------+---------------+
                                              | asyncpg
                                 +------------v---------------+
                                 |   PostgreSQL 16            |
                                 |   11 tables, native enums  |
                                 +-----------------------------+
```

**Why this split:** feature-based backend modules (`app/auth`, `app/booking`,
`app/search`, `app/payment`), not layer-based — each module owns its
models, schemas, service logic, and routes together, which is easier to
navigate solo and easier to hand off. See `docs/architecture.md` for the
full reasoning, including the seat-locking concurrency design.

---

## Quick Start (local dev, no Docker required)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (locally installed, or via Docker — see below)

### 1. Database

```bash
createdb ticket_booking
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set DB_HOST=localhost if running Postgres directly on your
# host (not in Docker). See the comment in .env.example -- this exact
# distinction caused a real bug during development (see decisions.md).

alembic upgrade head
python -m scripts.seed_data       # creates demo operators, routes, users

uvicorn app.main:app --reload
```

API docs: http://localhost:8000/api/docs

**Demo accounts** (created by the seed script):

| Role | Email | Password |
|---|---|---|
| Admin | admin@ticketbooking.pk | Admin@12345 |
| Customer | customer@example.com | Customer@123 |
| Operator | operator.bus@example.com | Operator@123 |

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

App: http://localhost:3000

### 4. (Optional) Docker Compose

```bash
docker compose up -d
```

This starts Postgres + backend together, with the backend's `DB_HOST`
automatically overridden to the Compose service name (`postgres`) rather
than `localhost` — see `docker-compose.yml` comments and `decisions.md`
for why this distinction matters and previously caused a real bug.

**Note:** this exact command has not been run in the environment this
project was built in (no Docker daemon available there). The config was
validated structurally (YAML parse, cross-referenced service names,
dependency graph) and the underlying database logic was verified against
a real, separately-installed PostgreSQL instance — but `docker compose up`
itself is unverified. Please run it and report back if anything's off;
it should work, but "should" isn't "verified" and this README won't
pretend otherwise.

---

## Running Tests

```bash
cd backend
pytest tests/ -v                              # 46 tests, SQLite-backed, fast
pytest tests/postgres/ -v                     # 3 tests, requires real Postgres
                                               # (set TEST_DATABASE_URL if not
                                               # using the default localhost:5432)
```

```bash
cd frontend
npx tsc --noEmit                              # strict type-check
npx next lint                                 # ESLint
npm run build                                 # production build
```

---

## Project Structure

```
ticket-booking-platform/
├── backend/
│   ├── app/
│   │   ├── auth/           # registration, JWT, email verification, RBAC
│   │   ├── search/         # schedule search and detail
│   │   ├── booking/        # seat locking, booking lifecycle, cancellation
│   │   ├── payment/        # gateway abstraction: mock, JazzCash, EasyPaisa
│   │   ├── operators/      # Operator/Vehicle/Route/Schedule/Seat models
│   │   └── common/         # shared enums, security, datetime utils, deps
│   ├── alembic/versions/   # one hand-written migration (0001_initial_schema)
│   ├── scripts/seed_data.py
│   └── tests/
│       ├── unit/           # 30+ tests, SQLite-backed
│       ├── integration/    # full HTTP-level flow via httpx ASGI transport
│       └── postgres/       # critical-path tests against REAL Postgres
├── frontend/
│   └── src/
│       ├── app/            # Next.js App Router pages
│       ├── components/     # shared UI (TextField, Button, SeatMap, etc.)
│       ├── store/          # Zustand: auth-store, booking-flow-store
│       ├── hooks/          # SWR-based data hooks
│       └── lib/            # typed API client, zod validation schemas
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── security.md
│   └── decisions.md        # what was found and fixed, and why -- read this
└── docker-compose.yml
```

---

## Known Limitations (stated plainly, not buried)

1. **No real payment gateway credentials.** `PAYMENT_PROVIDER=mock` by
   default. JazzCash and EasyPaisa gateway classes are structurally
   correct (matching each provider's documented HMAC-signing scheme) but
   raise `NotImplementedError` until real merchant credentials are set in
   `.env`. See `app/payment/gateways/`.
2. **`docker compose up` not run.** See Quick Start note above.
3. **No browser-driven frontend tests.** TypeScript strict-mode
   compilation, ESLint, production build, and full API-contract
   verification (via curl against a live backend) all passed — but no
   headless-browser or manual-click testing was performed. If something
   renders wrong in an actual browser, this is the most likely place.
4. **`expire_stale_bookings()` has no scheduler.** The function exists
   and is tested, but nothing currently calls it periodically. Pending
   bookings past their payment window won't auto-release seats until
   something (a cron job, APScheduler, etc.) is wired to call it.
5. **Refresh token lookup is O(n) in active sessions.** Documented in
   `app/auth/service.py::rotate_refresh_token`. Fine at MVP scale, not
   at scale — the fix is a fast indexed lookup hash alongside the slow
   bcrypt hash, not a rewrite.
6. **Operator dashboard and admin panel:** database models exist for
   operators, vehicles, routes; no API routes or UI were built for
   operators to manage their own fleet/schedules, or for admins to
   verify operators. Out of scope for this 2-day MVP.
7. **Next.js dependency:** pinned to `14.2.35` after patching a critical
   CVE found in the original `14.2.5` pin. Some high-severity advisories
   remain unresolved within the 14.x line; triaged as not applicable to
   features this app actually uses (see `docs/decisions.md`). A future
   major-version upgrade to Next 15 is a reasonable next step once there's
   time to regression-test the App Router changes it brings.

---

## License

Unlicensed / private project.
