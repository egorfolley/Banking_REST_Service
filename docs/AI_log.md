# AI logging

## Initial usage of Claude MODEL

for insturcttions + architecture

## Github Copilot for coding

Initial prompt:

```
Build a complete Banking REST Service for a take-home assessment. Production-grade, security-first.
Tech: FastAPI + SQLAlchemy 2.0 + SQLite (WAL mode, FK enforced) + Pydantic v2 + python-jose JWT + passlib bcrypt + pytest + Docker.

All endpoints under /api/v1. JWT Bearer auth on all protected routes.

DATABASE MODELS (UUID primary keys everywhere):
- users: email (unique), hashed_password, is_active
- account_holders: user_id (FK, unique), first_name, last_name, date_of_birth, phone, address, ssn_last_four (ONLY last 4 digits stored)
- accounts: holder_id (FK), account_number (unique, 10-digit), account_type (checking/savings), status (active/frozen/closed), balance, currency
- transactions: account_id (FK), transaction_type (deposit/withdrawal/transfer_in/transfer_out/fee), amount, balance_after, description, reference_id (links to transfer), status
- transfers: idempotency_key (UNIQUE), from_account_id, to_account_id, amount, description, status (pending/completed/failed), completed_at
- cards: account_id (FK), card_number_last_four, card_number_hash (SHA-256, NEVER store full number), card_type (debit/credit), status (active/frozen/cancelled), expiry_month, expiry_year, daily_limit
- audit_logs: user_id, action, resource_type, resource_id, details, ip_address

7 ROUTERS:
1. Auth: POST /signup (strong password: 8+ chars, upper, lower, digit, special), POST /login (same error for wrong email AND wrong password), POST /refresh, GET /me
2. Account Holders: POST / (create profile), GET /me, PUT /me
3. Accounts: POST / (with optional initial_deposit), GET /, GET /{id}, PATCH /{id}/status (can't close with non-zero balance)
4. Transactions: POST /{account_id}/deposit, POST /{account_id}/withdraw (check balance), GET /{account_id} with pagination (page, page_size) and optional transaction_type filter. Reject ops on frozen/closed accounts.
5. Transfers (MOST CRITICAL): POST / requires idempotency_key. If duplicate key, return existing transfer (don't process again). Verify sender owns source account. Destination can be any active account. ATOMIC: debit sender + credit receiver in single DB transaction, rollback both on failure. Create Transaction records on both sides linked via reference_id. Prevent self-transfer at schema validation level.
6. Cards: POST / (max 3 active per account), GET /, GET /{id}, PATCH /{id}/status, PATCH /{id}/limit
7. Statements: GET /{account_id}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD returns opening_balance, closing_balance, total_deposits, total_withdrawals, transaction_count, transaction list. Calculate opening balance from last transaction before start_date.

Use round(x, 2) on all balance calculations. Every endpoint verifies ownership: JWT → User → AccountHolder → Account.

```

## Creating a flow

```
Implement this user flow in order:
1) POST /auth/signup
2) POST /auth/login
3) GET /me
4) POST /accounts
5) GET /accounts
6) GET /accounts/{account_id}
7) POST /accounts/{account_id}/deposit (demo helper)
8) GET /accounts/{account_id}/transactions
9) POST /transfers (atomic transfer)
10) GET /accounts/{account_id}/statement?start=YYYY-MM-DD&end=YYYY-MM-DD
11) Optional cards endpoints

Business rules:
- Store money as integer cents (balance_cents, amount_cents)
- Only account owners can view/use their accounts
- Transfer validation: source != destination, amount > 0, sufficient funds, accounts active
- Transfer must be atomic and create transfer_out + transfer_in transaction records plus a transfer record
- Never return password hashes

Use Pydantic request/response schemas, SQLAlchemy ORM models, and service layer methods for business logic. Keep route handlers thin. Add pytest integration tests for auth, account creation, deposit, transfer, and statement retrieval.
```
