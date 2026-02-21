"""Account management tests."""
import pytest
from tests.conftest import auth, make_account, USER1


class TestCreateAccount:
    def test_create_checking_with_deposit(self, client, token1, holder1):
        r = client.post("/api/v1/accounts/", json={
            "account_type": "checking", "initial_deposit_cents": 50000
        }, headers=auth(token1))
        assert r.status_code == 201
        data = r.json()
        assert data["balance_cents"] == 50000
        assert data["account_type"] == "checking"
        assert len(data["account_number"]) == 10

    def test_create_account_zero_balance(self, client, token1, holder1):
        r = client.post("/api/v1/accounts/", json={"account_type": "savings"},
                        headers=auth(token1))
        assert r.status_code == 201
        assert r.json()["balance_cents"] == 0

    def test_without_token_returns_401(self, client, holder1):
        r = client.post("/api/v1/accounts/", json={"account_type": "checking"})
        assert r.status_code == 401

    def test_invalid_type_returns_422(self, client, token1, holder1):
        r = client.post("/api/v1/accounts/", json={"account_type": "crypto"},
                        headers=auth(token1))
        assert r.status_code == 422


class TestListAccounts:
    def test_list_own_accounts(self, client, token1, checking):
        r = client.get("/api/v1/accounts/", headers=auth(token1))
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()]
        assert checking["id"] in ids

    def test_does_not_leak_other_users_accounts(self, client, token1, token2, checking, savings2):
        r = client.get("/api/v1/accounts/", headers=auth(token1))
        ids = [a["id"] for a in r.json()]
        assert savings2["id"] not in ids


class TestGetAccount:
    def test_get_owned_account(self, client, token1, checking):
        r = client.get(f"/api/v1/accounts/{checking['id']}", headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["id"] == checking["id"]

    def test_get_nonowned_account_returns_404(self, client, token1, savings2):
        r = client.get(f"/api/v1/accounts/{savings2['id']}", headers=auth(token1))
        assert r.status_code == 404

    def test_get_nonexistent_returns_404(self, client, token1, holder1):
        r = client.get("/api/v1/accounts/00000000-0000-0000-0000-000000000000", headers=auth(token1))
        assert r.status_code == 404


class TestAccountStatus:
    def test_freeze_account(self, client, token1, checking):
        r = client.patch(f"/api/v1/accounts/{checking['id']}/status",
                         json={"status": "frozen"}, headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["status"] == "frozen"

    def test_unfreeze_account(self, client, token1, checking):
        client.patch(f"/api/v1/accounts/{checking['id']}/status",
                     json={"status": "frozen"}, headers=auth(token1))
        r = client.patch(f"/api/v1/accounts/{checking['id']}/status",
                         json={"status": "active"}, headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    def test_close_with_balance_fails(self, client, token1, checking):
        r = client.patch(f"/api/v1/accounts/{checking['id']}/status",
                         json={"status": "closed"}, headers=auth(token1))
        assert r.status_code == 400
        assert "balance" in r.json()["detail"].lower()

    def test_close_empty_account_succeeds(self, client, token1, holder1):
        acc = make_account(client, token1, "savings")
        r = client.patch(f"/api/v1/accounts/{acc['id']}/status",
                         json={"status": "closed"}, headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

    def test_non_owned_account_status_fails(self, client, token1, savings2):
        r = client.patch(f"/api/v1/accounts/{savings2['id']}/status",
                         json={"status": "frozen"}, headers=auth(token1))
        assert r.status_code == 404
