# AI Usage Report

## Overview

Development of this project combined ~2–3 hours of manual research, architecture design, and code review with AI-assisted prototyping and tooling. AI was used as an accelerator, not a replacement for decision-making. The workflow followed a deliberate sequence: understand the problem manually first, then use AI to scaffold, iterate, and validate.

Three AI tools were used across four stages:

| Tool                                   | Role                                        |
| -------------------------------------- | ------------------------------------------- |
| **Claude Opus 4.6** (claude.ai)  | Strategy evaluation, scope planning         |
| **Claude Code** (Sonnet 4.6 CLI) | Code scaffolding, test suite, documentation |
| **GitHub Copilot** (Grok Fast 1) | Inline debugging, UI tailoring, minor fixes |

---

## Stage 0 — Manual Research & Architecture Design

Before any AI was involved, the following was completed manually:

- Read the full assignment requirements and identified the most critical delivery areas: auth, atomic transfers, and ownership enforcement
- Decided on the technology stack (FastAPI, SQLAlchemy 2.0, SQLite, Pydantic v2, pytest) based on prior experience
- Sketched the data model relationships and the seven endpoint groups on paper
- Defined the constraint that money would be stored as **integer cents** to avoid float precision issues — this was a deliberate architectural choice made before any prompting

Only after forming a clear mental model was AI brought in.

---

## Stage 1 — Claude Opus 4.6: Strategy Validation

**Tool:** Claude Opus 4.6 via claude.ai
**Purpose:** Sanity-check the plan, identify blind spots, prioritise the 5-hour window

**Prompt used:**

```
ROLE
You are a helpful Forward-Deployed Engineer with 15 years of experience talking
to customers and building AI solutions. You have been working at top companies
like Invisible Tech, Palantir, Deloitte.

TASK
You are building a quick strategy plan and algorithm of actions, and explain
what to do. Provide additional things to deliver to maximize your chance of
success. Evaluate user's strategy and give critical feedback on the project
deliverables.

ASSIGNMENT
[pasted the full homework description]

USER STRATEGY
I have about 5 hours to complete this. Here's my initial plan:
- Hour 1: Set up project structure, database models, schemas
- Hour 2: Auth + account CRUD endpoints
- Hour 3: Transactions + transfers (most critical)
- Hour 4: Cards, statements, tests
- Hour 5: Docs, frontend bonus, polish and submit

What is the user missing?
```

**Output value:** Opus flagged that transfer atomicity and idempotency were the highest-risk items and recommended implementing them before cards or statements. It also suggested the token-type confusion attack (using a refresh token as an access token) which led to adding the `"type"` claim in both token payloads. This was incorporated into the final design.

**Manual decision retained:** The hour-by-hour plan was adjusted based on Opus feedback, but the final architecture decisions (integer cents, service-layer separation, SQLite WAL) were made by the developer.

---

## Stage 2 — Claude Code: Full Project Scaffold

**Tool:** Claude Code (Sonnet 4.6, CLI)
**Purpose:** Generate the initial project skeleton across all layers

**Prompt used (excerpt):**

```
Build a complete Banking REST Service - Production-grade, security-first.
Technology stack: FastAPI + SQLAlchemy 2.0 + SQLite (WAL mode, FK enforced)
+ Pydantic v2 + python-jose JWT + passlib bcrypt + pytest + Docker.

All endpoints under /api/v1. JWT Bearer auth on all protected routes.

DATABASE MODELS (UUID primary keys everywhere):
- users: email (unique), hashed_password, is_active
- account_holders: user_id (FK unique), first_name, last_name, date_of_birth,
  phone, address, ssn_last_four (ONLY last 4 digits stored)
- accounts: holder_id (FK), account_number (unique 10-digit), account_type
  (checking/savings), status (active/frozen/closed), balance_cents
- transactions: account_id (FK), transaction_type, amount_cents,
  balance_after_cents, description, reference_id, status
- transfers: idempotency_key (UNIQUE), from_account_id, to_account_id,
  amount_cents, description, status (pending/completed/failed), completed_at
- cards: account_id (FK), card_number_last_four, card_number_hash (SHA-256,
  NEVER store full number), card_type, status, expiry_month, expiry_year,
  daily_limit
- audit_logs: user_id, action, resource_type, resource_id, details, ip_address

[... 7 routers specified with full business rules ...]

Use round(x, 2) on all balance calculations. Every endpoint verifies
ownership: JWT → User → AccountHolder → Account.
```

**What Claude Code generated:**

- Full project directory structure (`app/api/v1/routes/`, `app/core/`, `app/models/`, `app/services/`, `app/utils/`)
- All seven SQLAlchemy models with `Mapped`/`mapped_column` (SQLAlchemy 2.0 style)
- All Pydantic v2 request/response schemas
- All route handlers with ownership checks
- `app/services/` layer separating business logic from routes
- `app/core/security.py` (bcrypt + JWT), `app/core/deps.py` (FastAPI dependencies)
- Dockerfile and docker-compose.yml
- Initial test scaffolding

**Iterations and corrections made:**

*Iteration 1 — Password validator regex bug:*
The initial scaffold generated the special-character regex with broken escape sequences due to heredoc/bash generation artefacts. The regex `r'[!@#$%^&*(),.?":{}|<>\\/...'` produced a syntax error at runtime. Resolved by rewriting the validator using a Python `set` of allowed characters — a simpler and more readable approach.

*Iteration 2 — passlib/bcrypt Python 3.12 incompatibility:*
Tests failed with `ValueError: password cannot be longer than 72 bytes`. This was a known compatibility issue between `passlib` and `bcrypt 4.x` on Python 3.12. Resolved by pinning `bcrypt==4.0.1` in `requirements.txt`.

---

## Stage 3 — GitHub Copilot (Grok Fast 1): Manual Debugging & UI

**Tool:** GitHub Copilot with Grok Fast 1 model
**Purpose:** Inline code walkthrough, frontend (UI) implementation, minor bug fixes

After the initial scaffold was generated by Claude Code, the codebase was walked through manually with Copilot as a pair-programming assistant for:

- **UI development:** The frontend (`frontend/` directory) — HTML/CSS/JS single-page banking client — was built iteratively with Copilot. The prompt pattern used was:
  ```
  Implement this user flow in order:
  1) POST /auth/signup
  2) POST /auth/login
  3) GET /me
  4) POST /accounts
  ...
  Business rules:
  - Store money as integer cents (balance_cents, amount_cents)
  - Only account owners can view/use their accounts
  ...
  ```
- **Debugging route responses:** Copilot was used to trace specific response shape mismatches between the frontend and API (e.g. field names, date formats).
- **Minor schema fixes:** Some field name inconsistencies between the scaffold and the intended spec were caught and corrected during this phase.

**Manual architecture overhaul (SC-1 through SC-5):**
After the initial AI-generated scaffold was reviewed, significant structural changes were made **manually without AI assistance**:

- Reorganised the folder structure (`app/routers/` → `app/api/v1/routes/`)
- Replaced `HTTPBearer` with `OAuth2PasswordBearer`
- Hardened the ownership dependency chain (`get_current_user` → `get_current_holder` → `get_account_for_user`)
- Refactored all monetary values to consistently use `_cents` suffix
- Added `app/models/enums.py` and `app/models/mixins.py` for cleaner separation
- Restructured config into `app/core/config.py` using pydantic-settings

These changes represent the developer's own architectural judgement applied on top of the AI-generated base.

---

## Stage 4 — Claude Code: Test Suite & Documentation

**Tool:** Claude Code (Sonnet 4.6, CLI)
**Purpose:** Recreate the test suite for the refactored architecture; write documentation

After the manual rewrite (SC-1 through SC-5), the original test files were replaced. Claude Code was given the new architecture to analyse and write a matching test suite:

- Read all new route files, schemas, and service files to understand the updated contracts
- Generated 8 test modules (75 tests total) using `TestClient` with per-test SQLite DB isolation via `dependency_overrides`
- Tests assert integer-cent values, 201 status for creates, and correct ownership isolation across two test users

**Challenges caught during test run:**

| Issue                                                     | Cause                                                                                       | Resolution                                                  |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `make_account()` helper asserted `status_code == 200` | Account creation route returns 201                                                          | Changed assertion to 201                                    |
| `test_without_token_returns_403` failing                | FastAPI's `OAuth2PasswordBearer` returns 401 (not 403) for missing tokens in this version | Updated all 6 tests and renamed methods to `_returns_401` |
| Two direct `POST /accounts/` tests still asserting 200  | Generated from an earlier pass before the 201 fix                                           | Updated individually                                        |

All 75 tests pass after corrections.

**Documentation generated by Claude Code:**

- `docs/DocSecurity.md` — full security considerations (this session)
- `README.md` — user flow Mermaid diagram added and syntax-corrected

---

## Stage 5 — GitHub Copilot: Final Polish

**Tool:** GitHub Copilot (Grok Fast 1)
**Purpose:** Final review pass, minor wording fixes, UI cleanup

Used for a final readthrough of route handlers and UI screens, catching minor inconsistencies in error messages and UI labels.

---

## Summary: What AI Did Well

- **Boilerplate elimination:** The full model/schema/router scaffold (thousands of lines) was generated in minutes, correctly applying SQLAlchemy 2.0 patterns and Pydantic v2 syntax.
- **Security prompting:** When security requirements were specified precisely, Claude applied them consistently — bcrypt, type-checked JWTs, SHA-256 card hashing, SSN minimisation — without needing to be reminded per-file.
- **Test generation:** Given the refactored architecture, Claude correctly inferred the new contracts (201 creates, integer cents, OAuth2 scheme) from reading the source files rather than the original spec.

## Summary: Where Manual Intervention Was Necessary

- **Architecture design:** The overall structure, the decision to use a service layer, the choice of integer cents over floats, and the `OAuth2PasswordBearer` vs `HTTPBearer` decision were all made by the developer.
- **Major refactor (SC-1 → SC-5):** Five commits of structural reorganisation were done manually after reviewing the AI scaffold.
- **Debugging runtime errors:** The bcrypt compatibility bug and the regex escaping issue both required understanding root causes that the AI did not flag upfront.
- **Test assertion corrections:** Several generated status-code assertions were wrong and required manual verification against the actual running API.
- **Prompt crafting:** Each AI prompt required careful specification of constraints (e.g. "same error for wrong email AND wrong password", "idempotency key must return existing record not a new one"). Vague prompts produced vague code.
