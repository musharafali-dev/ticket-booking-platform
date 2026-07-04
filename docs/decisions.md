# Engineering Decisions & Findings Log

This is not a features list. It's a record of the actual bugs found, the
trade-offs made under time pressure, and the reasoning behind each — so
that decisions made quickly during a 2-day build are still legible six
months from now.

---

## Bugs found during development (real, not hypothetical)

### 1. Alembic + Postgres native ENUM double-creation (critical)

**What happened:** The initial migration explicitly pre-created each
Postgres `ENUM` type via `enum.create(bind, checkfirst=True)`, then also
passed the same `Enum` object as a column type to `op.create_table()`.
Running the migration against real Postgres failed with
`type "user_role" already exists`.

**Root cause:** Alembic's `create_table()` auto-creates `Enum` column
types via an internal `before_create` DDL event that does not respect
`checkfirst=True` the same way `MetaData.create_all()` does. This is a
genuine SQLAlchemy/Alembic interaction quirk, not a Postgres bug.

**Why it went undetected for so long:** SQLite has no native `ENUM` type
at all — SQLAlchemy emulates it as `VARCHAR` + `CHECK` there — so this
Postgres-specific DDL code path was never exercised until the migration
was run against real Postgres for the first time, late in development.

**Fix:** Removed the explicit pre-creation loop. Since every enum in this
schema is used in exactly one `create_table()` call, letting
`create_table()` create it on first use is correct and sufficient. See
`backend/alembic/versions/0001_initial_schema.py` for the full comment
explaining this, so a future migration reusing an enum across multiple
tables doesn't reintroduce the bug via a different path.

**Lesson:** SQLite is not a faithful stand-in for Postgres-specific DDL
behavior. It's fine for testing business logic; it is not sufficient for
validating migrations.

---

### 2. Naive vs. timezone-aware datetime comparison (auth token expiry)

**What happened:** `EmailVerificationToken.expires_at` is declared
`DateTime(timezone=True)`, but SQLite (via `aiosqlite`) silently returns
a naive `datetime` on read regardless of that declaration. Comparing it
against `datetime.now(timezone.utc)` (aware) raised a `TypeError`.

**Fix:** Added `app/common/datetime_utils.py::is_expired()`, which
normalizes a naive datetime to UTC before comparing. Applied consistently
in `auth/service.py` and `payment/service.py` — anywhere a DB-sourced
datetime is compared against "now" in Python code (not inside a SQL
`WHERE` clause, which each database engine handles correctly natively
regardless of driver quirks).

**Re-verified against real Postgres** in `tests/postgres/`, which has
proper `TIMESTAMPTZ` support and should never have exhibited this bug —
confirming the fix works correctly on the backend where the bug never
existed, not just on the backend where the workaround was needed.

---

### 3. `session.rollback()` expires ALL attached ORM objects, not just the ones involved in the failed operation

**What happened:** `booking/service.py::create_booking` rolls back the
session when a seat lock conflict occurs (see concurrency design below).
A test that held a `Seat` object fetched before calling
`create_booking()`, then tried to read an attribute off it after a
conflicting call, hit `MissingGreenlet` — a SQLAlchemy async-driver error
indicating an attribute needed a lazy DB refetch outside a valid `await`
context.

**Root cause:** `expire_on_commit=False` only governs behavior on
commit. `session.rollback()` expires every attached object's attributes
regardless of that flag. This is documented SQLAlchemy behavior, easy to
miss.

**Fix:** Documented as an explicit caller contract on `create_booking()`
itself (see its docstring) — any caller holding a pre-fetched ORM object
across a call to this function must re-query by ID afterward rather than
trust the old reference. Fixed the test that surfaced this to do exactly
that, and verified no current route handler holds pre-fetched objects
across this call (grepped `booking/routes.py` to confirm).

---

### 4. EasyPaisa gateway computed a signature but never attached it to the request

**What happened:** `EasyPaisaGateway.initiate_payment()` computed
`signature = self._compute_hash(fields)` and then never used the
variable — the redirect URL was built without it. Caught by `ruff`'s
unused-variable check (F841), not by any test, since the mock gateway is
what's actually exercised in tests, not the EasyPaisa stub.

**Why this mattered:** if real EasyPaisa credentials were dropped in
later without noticing this, the integration would send an unsigned
checkout request — likely rejected outright, or worse, silently accepted
if EasyPaisa's server-side validation were ever lax.

**Fix:** Attached the signature to the redirect URL. Lesson: lint output
is not just style noise — F841 (unused variable) caught a real
security-relevant integration bug here.

---

### 5. `next@14.2.5` had multiple disclosed critical CVEs

**What happened:** `npm install` surfaced a critical-severity advisory
chain immediately (cache poisoning, authorization bypass, SSRF via
middleware) against the originally-pinned `14.2.5`.

**Fix:** Bumped to `14.2.35` — a patch-level fix within the 14.x line,
confirmed via `npm audit` to close the critical-severity findings with no
breaking API changes.

**What's still open:** several high-severity advisories remain against
`14.2.35` with no patched 14.x version available (`fixAvailable: N/A` in
`npm audit --json`) — the real fix path is Next 15.x, a major version
bump. Triaged the specific remaining advisory titles (next/image
optimizer, i18n routing, middleware, WebSockets, CSP-nonce script
injection) against features this app actually uses: none of them.
Residual risk is centered on Server Components DoS/cache-poisoning, which
is relevant since the App Router uses RSCs by default.

**Decision:** stay on patched `14.2.35` for this MVP rather than force an
unplanned major-version bump mid-build with no time to regression-test
Next 15's App Router changes. This is an explicit, documented trade-off,
not an oversight — flagged as a tracked post-MVP task.

---

### 6. A comment containing a literal comment-close sequence mid-string broke a file's parse

**What happened:** A docblock in `frontend/src/types/api.ts` referenced
a file glob path inside the comment. The literal close-comment characters
embedded in that path were parsed as the comment's own closing delimiter,
corrupting everything after it into invalid syntax. `tsc` caught this
immediately on the first compile.

**Fix:** Reworded the comment to avoid the literal sequence. Simple, but
a good reminder that comments are still code as far as the parser cares.

---

## Trade-offs made deliberately (not oversights)

### Seat-locking concurrency strategy: conditional UPDATE, not SELECT FOR UPDATE

**Chosen approach:** `lock_seats()` issues an `UPDATE seats SET
status='LOCKED' WHERE id=? AND status='AVAILABLE'` per seat, inside the
booking's transaction. If `rowcount == 0` for any seat, the exception
handler rolls back the whole transaction.

**Why this works without explicit row-locking:** Postgres applies each
UPDATE's WHERE clause atomically at the row level. Two concurrent
transactions racing for the same seat can never both match the same row
in their `WHERE status='AVAILABLE'` clause — exactly one succeeds
(rowcount=1), the other fails (rowcount=0). No SELECT FOR UPDATE, no
application-level lock, no Redis-based lock service required.

**Multi-seat bookings are all-or-nothing:** if any seat in a booking
request fails to lock, the entire transaction rolls back — including any
seats that did lock moments earlier in the same request. This relies on
the transaction boundary, not manual compensation logic.

**Verified, not just argued:**
- `tests/unit/test_booking_service.py::test_concurrent_booking_same_seat_only_one_wins` —
  2 concurrent asyncio tasks against SQLite (shared file, not in-memory,
  to approximate real concurrent connections)
- `tests/postgres/test_postgres_critical_paths.py::test_concurrent_booking_same_seat_real_postgres_mvcc` —
  the same test, 5 concurrent tasks, against real Postgres with real
  MVCC. Exactly 1 success, exactly 4 real 409 conflicts, confirmed by
  querying final DB state directly.

**What was explicitly not chosen:** a Redis-based short-lived seat lock
(considered, rejected as unjustified infrastructure complexity for an
MVP), and SELECT FOR UPDATE row-locking (would work, but the
conditional-UPDATE approach is simpler and achieves the same correctness
guarantee without holding a transaction-scoped lock open).

---

### Payment gateway abstraction

**Interface:** `app/payment/gateway.py::PaymentGatewayProvider` (ABC).
**Single swap point:** `app/payment/factory.py::get_payment_gateway()` —
the only place in the codebase that imports a concrete gateway class.
`PaymentService` and all route handlers depend solely on the interface.

**Why this matters concretely:** switching from mock to JazzCash in any
environment is a one-line `PAYMENT_PROVIDER=jazzcash` config change, not
a code change — this was an explicit requirement, not a nice-to-have.
Verify it yourself: `app/payment/service.py` never imports
`MockPaymentGateway`, `JazzCashGateway`, or `EasyPaisaGateway` directly.

**Stub quality:** the JazzCash and EasyPaisa classes are not empty
placeholders — they implement each provider's documented HMAC
request-signing scheme correctly (verified via round-trip signature
tests: sign, then verify, then confirm tampering is detected). What's
missing is real credentials and confirming exact field names/endpoints
against each provider's current merchant documentation, since payment
gateway APIs do change over time and this was built without live sandbox
access to either provider.

---

### Auth token storage: localStorage, with the trade-off stated explicitly

Access and refresh tokens are persisted via Zustand's `persist` middleware
to `localStorage`. This is convenient (session survives a page refresh)
but means a successful XSS on this origin could exfiltrate both tokens,
not just the access token — a stricter design keeps the refresh token
only in an httpOnly cookie, invisible to any JS on the page.

**Accepted for this MVP because:**
1. No third-party scripts are loaded, shrinking realistic XSS surface
2. Access tokens are short-lived (30 min)
3. Refresh tokens are already single-use/rotated server-side — a stolen
   token invalidates itself on next legitimate use, surfacing compromise
   rather than allowing silent indefinite reuse

**Flagged as a follow-up:** move refresh token issuance to an httpOnly,
Secure, SameSite=strict cookie set directly by the backend.

---

### DB_HOST: localhost vs. Docker service name

**What happened:** the root `.env.example` defaulted `DB_HOST=postgres`
(correct inside Docker Compose's network, where services resolve each
other by name) but the app, when run directly on a host machine outside
Docker, needs `DB_HOST=localhost`. Discovered because `pydantic-settings`
reads `.env` relative to the working directory the process is launched
from, not the repo root — so a root-level `.env` was silently not being
read at all when running the backend from `backend/`.

**Fix:** `backend/.env.example` now exists as its own template (where the
app actually runs from), and `docker-compose.yml` explicitly overrides
`DB_HOST=postgres` in the `environment:` block regardless of whatever the
mounted `.env` says — so Docker Compose is correct by construction, not
by remembering to edit the file correctly each time.

---

## What "verified" means in this project, precisely

Because verification claims are easy to overstate, here is exactly what
was and wasn't checked, and how:

| Claim | How verified |
|---|---|
| Backend unit logic correctness | 46 pytest tests against SQLite (fast iteration) |
| Backend correctness on the actual target DB | 3 additional pytest tests against a real, separately-installed PostgreSQL 16 instance, covering native enum enforcement, timezone handling, and 5-way concurrent booking |
| Full backend HTTP-level wiring | tests/integration/test_e2e_booking_flow.py — real HTTP requests via httpx's ASGI transport, not direct service calls |
| Migration correctness | Ran alembic upgrade head and alembic downgrade base against real Postgres, inspected resulting schema directly, not just checked exit codes |
| Frontend type safety | tsc --noEmit in strict mode + noUncheckedIndexedAccess, zero errors |
| Frontend lint | next lint (ESLint, next/core-web-vitals), zero warnings |
| Frontend build | next build, all 8 routes compile and prerender/route correctly |
| Frontend/backend contract | Full flow (register, login, search, book, pay, confirm) driven via curl against the real running backend, every JSON field traced against what frontend components actually destructure |
| CORS | Explicit OPTIONS preflight request with a real Origin header, confirming access-control-allow-origin matches — curl doesn't enforce CORS by default, so this required a deliberate extra check |
| Frontend in an actual browser | Not done — no headless browser tooling was available in the build environment |
| docker compose up | Not done — no Docker daemon was available in the build environment; config validated structurally only |

If you extend this project, the two "not done" rows are the highest-value
next verification steps before considering this production-ready.
