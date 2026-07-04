# Security

## What's implemented

- **Password hashing:** bcrypt via passlib, never plaintext, never logged.
- **JWT access tokens:** short-lived (30 min default), signed with
  SECRET_KEY (must be a strong 32+ char value in production — validated
  at startup via a pydantic validator in app/config.py, which raises if
  the default dev value is used with ENVIRONMENT=production).
- **Refresh tokens:** stored hashed (never plaintext) in the DB, single-use
  (rotated on every refresh — the old token is revoked immediately), so a
  stolen-but-unused token invalidates itself the moment the legitimate
  user refreshes again, surfacing the compromise rather than allowing
  silent indefinite replay.
- **RBAC:** require_role() FastAPI dependency factory, checked in the
  OpenAPI schema (visible in /api/docs), not hidden in ad-hoc if
  statements scattered through route bodies.
- **Account enumeration resistance:** login returns the identical error
  message and status code for "no such user" and "wrong password" —
  covered by a regression test
  (test_authenticate_nonexistent_user_same_error_as_wrong_password).
- **No stack traces leaked to clients:** a global exception handler
  (app/error_handlers.py) catches unhandled exceptions and returns a
  generic message, logging the real traceback server-side only — this
  matters because leaving DEBUG=true on by accident in production is a
  common, real way stack traces (revealing file paths, library versions)
  leak to attackers.
- **Native DB-level enum constraints:** every status field is a Postgres
  ENUM, not a free-text VARCHAR — the database itself rejects an invalid
  value, independent of whatever application code does or forgets to
  validate. Proven with a test that attempts to write an invalid enum
  value directly via SQL and confirms Postgres rejects it.
- **Payment signature verification:** JazzCash and EasyPaisa gateway stubs
  use hmac.compare_digest() for signature verification, not == — a naive
  equality check on a signature comparison is a timing side-channel that
  can, in principle, leak how many leading bytes of a forged signature
  matched.
- **Dependency vulnerability scanning performed at build time:** a
  critical CVE chain in next@14.2.5 was found via npm audit during
  initial dependency installation and patched before any further
  development — see decisions.md for the full account, including what
  residual risk remains and why it was accepted for this MVP.
- **CORS explicitly scoped:** CORS_ORIGINS is a specific allowlist
  (http://localhost:3000 in dev), not a wildcard.

## What's NOT implemented (explicit gaps, not silent omissions)

- **Rate limiting:** no actual rate limiter is wired in yet (e.g. on
  /auth/login to slow brute-force attempts). The FastAPI route structure
  would support adding slowapi or similar without much rework, but
  nothing is active today.
- **Multi-factor authentication:** not implemented.
- **CSP headers / security headers middleware:** not added
  (X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security,
  etc.). Straightforward to add as middleware in app/main.py; not done
  for this MVP.
- **httpOnly cookie-based refresh tokens:** tokens currently live in
  localStorage on the frontend (see docs/decisions.md for the full
  trade-off reasoning). This is the single most impactful frontend
  security improvement to make before this goes anywhere near production
  traffic with real user data.
- **Audit logging:** an earlier, separate planning pass described an
  audit_logs table; it was cut from the actual schema as YAGNI for a
  2-day MVP. If this becomes a compliance-relevant system (handling real
  payments, PII at scale), audit logging should be added back
  deliberately, not as an afterthought.
- **Real payment gateway credentials:** by construction, no real money can
  move through this system as shipped (PAYMENT_PROVIDER=mock). This is a
  safety feature during development, not just a limitation — do not
  configure real JazzCash/EasyPaisa credentials without also completing a
  proper security review of the callback-verification paths
  (verify_callback_signature in each gateway) against a real sandbox
  environment first.

## Threat model notes specific to this domain

**Double-booking is the highest-value attack/failure surface for a
booking platform** — worse than most XSS or CSRF scenarios in terms of
direct business impact (a sold seat that two people paid for is a
refund, a support ticket, and a trust problem, not just a data
inconsistency). This is why the seat-locking design received the most
verification effort in this project — see decisions.md for the specific
concurrency tests run against real Postgres.

**CNIC / passport number fields exist in the schema** (User.cnic_number,
BookingPassenger.id_number) but have no field-level encryption at rest
in the current implementation — they're stored as plain columns. For a
real Pakistani platform handling government ID numbers, encrypting these
at the application layer (not just relying on disk-level encryption)
should be a pre-production requirement, not an optional hardening step.
