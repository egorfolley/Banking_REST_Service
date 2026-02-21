"""Transfer endpoint tests — the most critical flow."""
import uuid
import pytest
from tests.conftest import auth


class TestTransferSuccess:
    def test_transfer_updates_both_balances(self, client, token1, token2, checking, savings2):
        key = str(uuid.uuid4())
        r = client.post("/api/v1/transfers/", json={
            "idempotency_key": key,
            "from_account_id": checking["id"],
            "to_account_id": savings2["id"],
            "amount_cents": 20000,
        }, headers=auth(token1))
        assert r.status_code == 201
        assert r.json()["status"] == "completed"

        sender = client.get(f"/api/v1/accounts/{checking['id']}", headers=auth(token1)).json()
        assert sender["balance_cents"] == 80000  # 100000 - 20000

        receiver = client.get(f"/api/v1/accounts/{savings2['id']}", headers=auth(token2)).json()
        assert receiver["balance_cents"] == 70000  # 50000 + 20000

    def test_transfer_creates_two_transaction_records(self, client, token1, token2, checking, savings2):
        key = str(uuid.uuid4())
        client.post("/api/v1/transfers/", json={
            "idempotency_key": key,
            "from_account_id": checking["id"],
            "to_account_id": savings2["id"],
            "amount_cents": 5000,
        }, headers=auth(token1))

        sender_txs = client.get(f"/api/v1/transactions/{checking['id']}", headers=auth(token1)).json()
        receiver_txs = client.get(f"/api/v1/transactions/{savings2['id']}", headers=auth(token2)).json()

        sender_types = [t["transaction_type"] for t in sender_txs["items"]]
        receiver_types = [t["transaction_type"] for t in receiver_txs["items"]]

        assert "transfer_out" in sender_types
        assert "transfer_in" in receiver_types


class TestTransferIdempotency:
    def test_same_key_not_debited_twice(self, client, token1, token2, checking, savings2):
        key = str(uuid.uuid4())
        payload = {
            "idempotency_key": key,
            "from_account_id": checking["id"],
            "to_account_id": savings2["id"],
            "amount_cents": 10000,
        }
        r1 = client.post("/api/v1/transfers/", json=payload, headers=auth(token1))
        r2 = client.post("/api/v1/transfers/", json=payload, headers=auth(token1))
        assert r1.status_code == r2.status_code == 201
        assert r1.json()["id"] == r2.json()["id"]

        sender = client.get(f"/api/v1/accounts/{checking['id']}", headers=auth(token1)).json()
        assert sender["balance_cents"] == 90000  # debited only once


class TestTransferFailures:
    def test_insufficient_funds(self, client, token1, token2, checking, savings2):
        r = client.post("/api/v1/transfers/", json={
            "idempotency_key": str(uuid.uuid4()),
            "from_account_id": checking["id"],
            "to_account_id": savings2["id"],
            "amount_cents": 9_999_999,
        }, headers=auth(token1))
        assert r.status_code == 400
        assert "fund" in r.json()["detail"].lower()

    def test_self_transfer_rejected(self, client, token1, checking):
        r = client.post("/api/v1/transfers/", json={
            "idempotency_key": str(uuid.uuid4()),
            "from_account_id": checking["id"],
            "to_account_id": checking["id"],
            "amount_cents": 1000,
        }, headers=auth(token1))
        assert r.status_code == 422

    def test_transfer_from_other_users_account_rejected(self, client, token2, checking, savings2):
        r = client.post("/api/v1/transfers/", json={
            "idempotency_key": str(uuid.uuid4()),
            "from_account_id": checking["id"],
            "to_account_id": savings2["id"],
            "amount_cents": 1000,
        }, headers=auth(token2))
        assert r.status_code == 404

    def test_transfer_to_nonexistent_account(self, client, token1, checking):
        r = client.post("/api/v1/transfers/", json={
            "idempotency_key": str(uuid.uuid4()),
            "from_account_id": checking["id"],
            "to_account_id": "00000000-0000-0000-0000-000000000000",
            "amount_cents": 1000,
        }, headers=auth(token1))
        assert r.status_code == 404

    def test_transfer_without_token_fails(self, client, checking, savings2):
        r = client.post("/api/v1/transfers/", json={
            "idempotency_key": str(uuid.uuid4()),
            "from_account_id": checking["id"],
            "to_account_id": savings2["id"],
            "amount_cents": 1000,
        })
        assert r.status_code == 401

    def test_transfer_from_frozen_account_fails(self, client, token1, token2, checking, savings2):
        client.patch(f"/api/v1/accounts/{checking['id']}/status",
                     json={"status": "frozen"}, headers=auth(token1))
        r = client.post("/api/v1/transfers/", json={
            "idempotency_key": str(uuid.uuid4()),
            "from_account_id": checking["id"],
            "to_account_id": savings2["id"],
            "amount_cents": 1000,
        }, headers=auth(token1))
        assert r.status_code == 400

    def test_transfer_to_frozen_account_fails(self, client, token1, token2, checking, savings2):
        client.patch(f"/api/v1/accounts/{savings2['id']}/status",
                     json={"status": "frozen"}, headers=auth(token2))
        r = client.post("/api/v1/transfers/", json={
            "idempotency_key": str(uuid.uuid4()),
            "from_account_id": checking["id"],
            "to_account_id": savings2["id"],
            "amount_cents": 1000,
        }, headers=auth(token1))
        assert r.status_code == 400
