"""Deposit, withdrawal and transaction listing tests."""
import pytest
from tests.conftest import auth, make_account


class TestDeposit:
    def test_deposit_updates_balance(self, client, token1, checking):
        acc_id = checking["id"]
        r = client.post(f"/api/v1/transactions/{acc_id}/deposit",
                        json={"amount_cents": 20000, "description": "Paycheck"},
                        headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["amount_cents"] == 20000
        assert r.json()["balance_after_cents"] == 120000  # 100000 + 20000

    def test_deposit_creates_transaction_record(self, client, token1, checking):
        acc_id = checking["id"]
        client.post(f"/api/v1/transactions/{acc_id}/deposit",
                    json={"amount_cents": 5000}, headers=auth(token1))
        r = client.get(f"/api/v1/transactions/{acc_id}", headers=auth(token1))
        assert r.status_code == 200
        types = [t["transaction_type"] for t in r.json()["items"]]
        assert "deposit" in types

    def test_deposit_zero_fails(self, client, token1, checking):
        r = client.post(f"/api/v1/transactions/{checking['id']}/deposit",
                        json={"amount_cents": 0}, headers=auth(token1))
        assert r.status_code == 422

    def test_deposit_negative_fails(self, client, token1, checking):
        r = client.post(f"/api/v1/transactions/{checking['id']}/deposit",
                        json={"amount_cents": -100}, headers=auth(token1))
        assert r.status_code == 422

    def test_deposit_on_frozen_account_fails(self, client, token1, checking):
        acc_id = checking["id"]
        client.patch(f"/api/v1/accounts/{acc_id}/status", json={"status": "frozen"},
                     headers=auth(token1))
        r = client.post(f"/api/v1/transactions/{acc_id}/deposit",
                        json={"amount_cents": 1000}, headers=auth(token1))
        assert r.status_code == 400

    def test_deposit_on_non_owned_account_fails(self, client, token1, savings2):
        r = client.post(f"/api/v1/transactions/{savings2['id']}/deposit",
                        json={"amount_cents": 1000}, headers=auth(token1))
        assert r.status_code == 404


class TestWithdrawal:
    def test_withdraw_updates_balance(self, client, token1, checking):
        acc_id = checking["id"]
        r = client.post(f"/api/v1/transactions/{acc_id}/withdraw",
                        json={"amount_cents": 30000}, headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["balance_after_cents"] == 70000  # 100000 - 30000

    def test_withdraw_insufficient_funds(self, client, token1, checking):
        r = client.post(f"/api/v1/transactions/{checking['id']}/withdraw",
                        json={"amount_cents": 999999}, headers=auth(token1))
        assert r.status_code == 400
        assert "funds" in r.json()["detail"].lower()

    def test_withdraw_from_frozen_fails(self, client, token1, checking):
        acc_id = checking["id"]
        client.patch(f"/api/v1/accounts/{acc_id}/status", json={"status": "frozen"},
                     headers=auth(token1))
        r = client.post(f"/api/v1/transactions/{acc_id}/withdraw",
                        json={"amount_cents": 1000}, headers=auth(token1))
        assert r.status_code == 400

    def test_withdraw_from_closed_fails(self, client, token1, holder1):
        acc = make_account(client, token1)
        acc_id = acc["id"]
        client.patch(f"/api/v1/accounts/{acc_id}/status", json={"status": "closed"},
                     headers=auth(token1))
        r = client.post(f"/api/v1/transactions/{acc_id}/withdraw",
                        json={"amount_cents": 1}, headers=auth(token1))
        assert r.status_code == 400


class TestTransactionList:
    def test_list_transactions_success(self, client, token1, checking):
        acc_id = checking["id"]
        client.post(f"/api/v1/transactions/{acc_id}/deposit",
                    json={"amount_cents": 5000}, headers=auth(token1))
        r = client.get(f"/api/v1/transactions/{acc_id}", headers=auth(token1))
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert data["total"] >= 1

    def test_pagination(self, client, token1, checking):
        acc_id = checking["id"]
        for _ in range(5):
            client.post(f"/api/v1/transactions/{acc_id}/deposit",
                        json={"amount_cents": 100}, headers=auth(token1))
        # 5 deposits + 1 initial = 6 total
        r = client.get(f"/api/v1/transactions/{acc_id}?page=1&page_size=3",
                       headers=auth(token1))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 6
        assert len(data["items"]) == 3

    def test_filter_by_type(self, client, token1, checking):
        acc_id = checking["id"]
        client.post(f"/api/v1/transactions/{acc_id}/deposit",
                    json={"amount_cents": 1000}, headers=auth(token1))
        client.post(f"/api/v1/transactions/{acc_id}/withdraw",
                    json={"amount_cents": 500}, headers=auth(token1))
        r = client.get(f"/api/v1/transactions/{acc_id}?transaction_type=withdrawal",
                       headers=auth(token1))
        assert r.status_code == 200
        assert all(t["transaction_type"] == "withdrawal" for t in r.json()["items"])

    def test_non_owned_account_returns_404(self, client, token1, savings2):
        r = client.get(f"/api/v1/transactions/{savings2['id']}", headers=auth(token1))
        assert r.status_code == 404
