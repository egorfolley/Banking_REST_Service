# Security Considerations

This document describes the security protections implemented in the Banking REST Service, the risks that were considered during design, and what is intentionally left out of scope for this project stage.

---

## 1. Protections Implemented

### 1.1 Password Security

- **bcrypt hashing** — passwords are never stored in plaintext. `passlib[bcrypt]` computes a salted bcrypt hash before writing to the database. bcrypt is intentionally slow, making offline brute-force attacks expensive.
- **Strength enforcement** — the `validate_password` validator (`app/utils/validators.py`) rejects passwords that do not contain at least one uppercase letter, one lowercase letter, one digit, one special character, and a minimum length of 8 characters. This is enforced at the Pydantic schema layer before any database interaction.

### 1.2 JWT Authentication

- **Dual-token scheme** — the API issues two JWTs on login/signup:
  - *Access token* — short-lived (30 minutes). Used on every authenticated request.
  - *Refresh token* — longer-lived (7 days). Used only to obtain a new access token via `POST /auth/refresh`.
- **Token type claim** — every token carries a `"type"` claim (`"access"` or `"refresh"`). The `get_current_user` dependency rejects any token whose type is not `"access"`, and the `/refresh` endpoint rejects any token whose type is not `"refresh"`. This prevents an attacker who intercepts a refresh token from using it directly as an access token.
- **Algorithm pinned** — HS256 is explicitly specified in both encoding (`jwt.encode`) and decoding (`jwt.decode`). Passing the algorithm list to `decode` prevents the `"alg": "none"` attack.
- **Expiry enforced** — `python-jose` validates the `exp` claim on every decode. An expired token is rejected with HTTP 401.

### 1.3 Email Enumeration Prevention

The login endpoint (`POST /auth/login`) evaluates wrong-email and wrong-password cases in a single condition:

```python
if not user or not verify_password(payload.password, user.hashed_password):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

Both failure modes return the same status code and the same error message, making it impossible for an attacker to determine whether a given email address has an account.

### 1.4 Card PAN Protection

Full card numbers are never stored. When a card is issued, `card_utils.py` produces:

| Stored field              | Value                              |
| ------------------------- | ---------------------------------- |
| `card_number_last_four` | Last 4 digits (display only)       |
| `card_number_hash`      | SHA-256 hex digest of the full PAN |

Only `card_number_last_four` is returned in API responses. The SHA-256 hash allows duplicate-card detection without storing the sensitive number.

### 1.5 PII Minimisation — SSN

Only the last four digits of a Social Security Number are accepted and stored (`ssn_last_four`). The full SSN is never sent to or retained by the service. The field is validated to be exactly 4 digits by `validate_ssn_last_four`.

### 1.6 Resource Ownership Enforcement

Every endpoint that accesses an account, transaction, card, or statement performs a database-level ownership check. The `get_account_for_user` dependency (`app/core/deps.py`) joins `accounts → account_holders → users` and filters by the authenticated user's ID:

```python
select(Account)
    .join(AccountHolder, Account.holder_id == AccountHolder.id)
    .where(Account.id == account_id, AccountHolder.user_id == current_user.id)
```

A request for a resource that exists but belongs to another user returns HTTP 404 (not 403), to avoid leaking the existence of the resource.

### 1.7 Transfer Idempotency

Transfers require a client-supplied `idempotency_key`. The key has a UNIQUE database constraint. If a second request arrives with the same key, the service returns the original transfer record without re-debiting the source account. This prevents double charges caused by network retries.

### 1.8 Audit Logging

Sign-up, login, and key account mutations are written to an `audit_logs` table, recording the `user_id`, action type, affected resource, timestamp, and client IP address. This provides a tamper-visible trail for post-incident review.

### 1.9 Input Validation at the Schema Layer

All request bodies are validated by Pydantic v2 before reaching any route handler. Invalid types, missing required fields, or values that fail custom validators return HTTP 422 automatically, preventing malformed data from reaching the database.

### 1.10 Database Integrity

SQLite is configured with:

- `PRAGMA foreign_keys = ON` — enforces referential integrity on every connection.
- `PRAGMA journal_mode = WAL` — provides safe concurrent reads alongside writes.

---

## 2. Risks Considered

| Risk                                         | Mitigation                                                                                             |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Password cracking after DB breach            | bcrypt with per-password salt; cost factor makes offline attacks slow                                  |
| Account takeover via token theft             | Short access-token lifetime (30 min) limits the window; refresh tokens are not usable as access tokens |
| Replay of JWT                                | `exp` claim enforced on every decode                                                                 |
| Email enumeration via login                  | Identical error for wrong email and wrong password                                                     |
| Horizontal privilege escalation              | Ownership checked at the DB query level on every resource access                                       |
| Duplicate/double-charge on retried transfers | Idempotency key with UNIQUE constraint                                                                 |
| SQL injection                                | SQLAlchemy ORM uses parameterised queries throughout; raw SQL is not used                              |
| PAN exposure in a data breach                | Full card number never persisted; SHA-256 hash and last-4 only                                         |
| Full SSN exposure                            | Only last-4 accepted and stored                                                                        |
| Token confusion (access ↔ refresh)          | Explicit `type` claim checked in every token consumer                                                |
| Weak user-chosen passwords                   | Enforced complexity rules at signup                                                                    |

---

## 3. Intentionally Out of Scope

The following security controls are **not** implemented. They are deliberately deferred because this is a take-home prototype rather than a production system.

### 3.1 Rate Limiting & Brute-Force Protection

There is no throttling on login attempts, signup attempts, or any API endpoint. A production deployment should add rate limiting at the API gateway or reverse-proxy layer (e.g. nginx `limit_req`, AWS WAF, Cloudflare).

### 3.2 HTTPS / TLS

The service binds on plain HTTP. TLS termination is expected to be handled by the infrastructure layer (reverse proxy, cloud load balancer). Never run this service on a public network without TLS in front of it.

### 3.3 Token Revocation

JWTs are stateless. Logging out does not invalidate the access token — it will remain valid until its `exp` is reached. A production system would store a revocation list (e.g. in Redis) or switch to shorter-lived tokens with server-side session state.

### 3.4 CORS Policy

`cors_origins` defaults to `["*"]` in `app/core/config.py`. This must be restricted to known frontend origins before any public deployment.

### 3.5 Multi-Factor Authentication

No MFA or step-up authentication is implemented.

### 3.6 JWT Secret Rotation

There is a single `JWT_SECRET_KEY`. Rotating it invalidates all active sessions simultaneously. A production system would support multiple active keys with a key-ID (`kid`) header to allow graceful rotation.

### 3.7 Full PCI DSS Compliance

Storing even a SHA-256 hash and last-4 of a PAN is not sufficient for PCI DSS compliance in production. A compliant implementation would tokenise card numbers using a PCI-certified vault (e.g. Stripe, Braintree) and never touch the raw PAN in application code.

### 3.8 Audit Log Integrity

Audit logs are stored in the same SQLite database as application data. A compromised database means logs can be altered. A production system should ship logs to a separate, append-only store (e.g. a SIEM or immutable object storage).

### 3.9 Secret Management

Secrets (`JWT_SECRET_KEY`) are loaded from a `.env` file via `pydantic-settings`. A production deployment should pull secrets from a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) rather than a file on disk.
