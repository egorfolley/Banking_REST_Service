"""Statement endpoint tests."""
import pytest
from datetime import date, timedelta
from tests.conftest import auth


def _today():
    return date.today().isoformat()

def _past(days=30):
    return (date.today() - timedelta(days=days)).isoformat()

def _future(days=365):
    return (date.today() + timedelta(days=days)).isoformat()


class TestStatements:
    def test_statement_with_transactions(self, client, token1, checking):
        acc_id = checking["id"]
        client.post(f"/api/v1/transactions/{acc_id}/deposit",
                    json={"amount_cents": 40000}, headers=auth(token1))
        client.post(f"/api/v1/transactions/{acc_id}/withdraw",
                    json={"amount_cents": 10000}, headers=auth(token1))

        r = client.get(f"/api/v1/statements/{acc_id}",
                       params={"start": _past(), "end": _future()},
                       headers=auth(token1))
        assert r.status_code == 200
        data = r.json()
        # initial deposit (100000) + deposit (40000) + withdrawal (10000) = 3 transactions
        assert data["transaction_count"] == 3
        assert data["total_deposits_cents"] == 140000  # 100000 + 40000
        assert data["total_withdrawals_cents"] == 10000
        assert data["closing_balance_cents"] == 130000

    def test_statement_empty_range(self, client, token1, checking):
        acc_id = checking["id"]
        r = client.get(f"/api/v1/statements/{acc_id}",
                       params={"start": "2000-01-01", "end": "2000-12-31"},
                       headers=auth(token1))
        assert r.status_code == 200
        data = r.json()
        assert data["transaction_count"] == 0
        assert data["opening_balance_cents"] == 0
        assert data["closing_balance_cents"] == 0

    def test_statement_invalid_date_range(self, client, token1, checking):
        acc_id = checking["id"]
        r = client.get(f"/api/v1/statements/{acc_id}",
                       params={"start": "2025-12-31", "end": "2025-01-01"},
                       headers=auth(token1))
        assert r.status_code == 400

    def test_statement_non_owned_account_fails(self, client, token1, savings2):
        r = client.get(f"/api/v1/statements/{savings2['id']}",
                       params={"start": _past(), "end": _future()},
                       headers=auth(token1))
        assert r.status_code == 404

    def test_statement_without_token_fails(self, client, checking):
        r = client.get(f"/api/v1/statements/{checking['id']}",
                       params={"start": _past(), "end": _future()})
        assert r.status_code == 401
