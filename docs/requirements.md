# Requirements

## Functional scope (agreed for the 2-day MVP)

1. User registration with email verification
2. Login with JWT access + refresh tokens, RBAC (CUSTOMER / OPERATOR / ADMIN)
3. Search schedules by departure city, arrival city, date, and transport type
4. View a schedule's seat map with live availability
5. Select seats, enter passenger details, and create a booking
6. Pay for a booking via a payment gateway abstraction (mock in dev; JazzCash
   and EasyPaisa as structurally-correct stubs pending real credentials)
7. View booking confirmation and booking history
8. Cancel a booking, releasing its seats back to availability
9. Minimal profile view (display-only)

## Explicitly out of scope for this MVP

- Operator dashboard (fleet/route/schedule management UI)
- Admin panel (operator verification, dispute resolution, analytics)
- Reviews and ratings
- Coupons/discounts
- SMS notifications (email only, and only via a console-logging dev backend)
- Multi-language support (English only)
- Real payment gateway credentials

## Non-functional requirements

- **Correctness under concurrency:** two users must never be able to book
  the same seat. This is the single hardest correctness requirement in the
  system and is treated accordingly — see `decisions.md` for the design
  and the tests that prove it against real Postgres.
- **Security:** JWT-based auth, bcrypt password hashing, rate-limiting-ready
  request structure (not yet wired to an actual rate limiter — flagged as
  a follow-up), no secrets in source control, dependency vulnerability
  scanning performed at build time (see `security.md`).
- **Maintainability:** feature-based module boundaries, one clear
  swap-point for the payment gateway, tests that exercise both the fast
  development database (SQLite) and the real target database (Postgres).

## Demo data

`backend/scripts/seed_data.py` creates:
- 1 admin, 1 customer, 3 operators (bus/train/airline) — see README for
  credentials
- 10 real Pakistani city-pair routes (Karachi to Lahore, Lahore to
  Islamabad, etc.)
- 7 days of schedules per route
- Full seat inventory per schedule (5,530 seats total across all schedules)
