"""
Shared fixtures for the banking REST service test suite.

Architecture notes:
- Signup (POST /auth/signup) returns {access_token, refresh_token} directly
- All amounts in integer CENTS (100 = $1.00)
- OAuth2PasswordBearer: missing token → 401, bad token → 401
- Duplicate email → 400
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.deps import get_db
from app.db.base import Base
from app.main import app

# ── In-memory test DB ────────────────────────────────────────────────────────
TEST_DB = "sqlite:///./test_banking.db"
_engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})


@event.listens_for(_engine, "connect")
def _pragmas(conn, _):
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA journal_mode=WAL")
    cur.close()


_Session = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def _reset_db():
    import app.models  # noqa: ensure all models registered
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db(_reset_db):
    session = _Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers ──────────────────────────────────────────────────────────────────

def signup_and_login(client, email: str, password: str) -> str:
    """Register + return access token."""
    r = client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_holder(client, token: str, **overrides) -> dict:
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "date_of_birth": "1990-01-15",
        "phone": "+14155550100",
        "address": "1 Market St, San Francisco, CA 94105",
        "ssn_last_four": "1234",
        **overrides,
    }
    r = client.post("/api/v1/account-holders/", json=payload, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def make_account(client, token: str, account_type="checking", initial_deposit_cents=0) -> dict:
    body = {"account_type": account_type}
    if initial_deposit_cents:
        body["initial_deposit_cents"] = initial_deposit_cents
    r = client.post("/api/v1/accounts/", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


# ── Layered fixtures ─────────────────────────────────────────────────────────

USER1 = ("alice@example.com", "AlicePass1!")
USER2 = ("bob@example.com", "BobPass2@")


@pytest.fixture()
def token1(client):
    return signup_and_login(client, *USER1)


@pytest.fixture()
def token2(client):
    return signup_and_login(client, *USER2)


@pytest.fixture()
def holder1(client, token1):
    return make_holder(client, token1)


@pytest.fixture()
def holder2(client, token2):
    return make_holder(client, token2, first_name="Bob", last_name="Jones",
                       ssn_last_four="5678", phone="+14155550200",
                       address="2 Broadway, New York, NY 10004")


@pytest.fixture()
def checking(client, token1, holder1):
    return make_account(client, token1, "checking", initial_deposit_cents=100_000)  # $1000


@pytest.fixture()
def savings2(client, token2, holder2):
    return make_account(client, token2, "savings", initial_deposit_cents=50_000)   # $500
