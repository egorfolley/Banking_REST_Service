# Roadmap

This document outlines concrete next steps to move the service from a take-home prototype to a production-ready system. Items are grouped by priority.

---

## Phase 1 — Production Hardening (Immediate)

| Item                              | Why                                                                                                            |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Replace SQLite with PostgreSQL    | SQLite has no concurrent writes; Postgres handles multi-user load and provides proper ACID guarantees at scale |
| Add Alembic migrations            | Schema changes currently require dropping and recreating the DB; migrations enable safe, versioned upgrades    |
| Lock down CORS                    | `cors_origins = ["*"]` must be restricted to known frontend origins before any public exposure               |
| Enforce HTTPS at app level        | Currently relies on infra; add an HTTP→HTTPS redirect middleware for non-containerised deployments            |
| Move secrets to a secrets manager | `JWT_SECRET_KEY` in `.env` should be pulled from AWS Secrets Manager, Vault, or equivalent at startup      |

---

## Phase 2 — Security & Reliability

| Item                            | Why                                                                                                                   |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Rate limiting on auth endpoints | Login and signup have no throttling; brute-force attacks are currently unconstrained                                  |
| Token revocation on logout      | JWTs remain valid until expiry; a Redis-backed blocklist or short-lived tokens + server sessions would close this gap |
| Refresh token rotation          | Issue a new refresh token on each `/refresh` call and invalidate the previous one to limit theft window             |
| Idempotency key expiry          | Currently idempotency keys are stored forever; add a TTL (e.g. 24 h) and a cleanup job                                |
| Structured logging              | Replace print-based debugging with JSON-structured logs (e.g.`structlog`) for easier querying in production         |

---

## Phase 3 — Feature Completeness

| Item                            | Why                                                                                                                               |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Card transaction processing     | Cards exist but no endpoint links a card to a transaction; add `POST /cards/{id}/charge` with daily-limit enforcement           |
| Scheduled / recurring transfers | Allow users to set up standing orders between their accounts                                                                      |
| Notifications                   | Email or webhook alerts for deposits, withdrawals, and low-balance events                                                         |
| Multi-currency support          | `currency` is not currently stored on accounts; add a `currency` column and FX conversion service                             |
| Account statements as PDF       | The statement endpoint returns JSON; a PDF export (e.g. via `reportlab` or `weasyprint`) would be a useful client deliverable |

---

## Phase 4 — Operational Maturity

| Item               | Why                                                                                                                           |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| CI/CD pipeline     | Add GitHub Actions: lint → test → build Docker image → push to registry on merge to main                                   |
| Observability      | Add Prometheus metrics (`/metrics`) and a health endpoint that checks DB connectivity                                       |
| Horizontal scaling | Swap SQLite for Postgres and make the app stateless (no local file state) so multiple replicas can run behind a load balancer |
| Admin API          | Internal endpoints for user deactivation, account freezing, and audit log queries — separate from the customer-facing API    |
