"""Account-holder profile tests."""
import pytest
from tests.conftest import auth, make_holder, USER1


class TestCreateProfile:
    def test_create_profile_success(self, client, token1):
        r = client.post("/api/v1/account-holders/", json={
            "first_name": "Alice", "last_name": "Smith",
            "date_of_birth": "1990-01-15", "phone": "+14155550100",
            "address": "1 Market St, San Francisco, CA 94105", "ssn_last_four": "1234",
        }, headers=auth(token1))
        assert r.status_code == 201
        data = r.json()
        assert data["first_name"] == "Alice"
        assert data["ssn_last_four"] == "1234"

    def test_duplicate_profile_rejected(self, client, token1, holder1):
        r = client.post("/api/v1/account-holders/", json={
            "first_name": "Alice", "last_name": "Smith",
            "date_of_birth": "1990-01-15", "phone": "+14155550100",
            "address": "1 Market St, San Francisco, CA 94105", "ssn_last_four": "1234",
        }, headers=auth(token1))
        assert r.status_code == 400

    def test_invalid_ssn_rejected(self, client, token1):
        r = client.post("/api/v1/account-holders/", json={
            "first_name": "Alice", "last_name": "Smith",
            "date_of_birth": "1990-01-15", "phone": "+14155550100",
            "address": "1 Market St, San Francisco, CA 94105", "ssn_last_four": "12X4",
        }, headers=auth(token1))
        assert r.status_code == 422

    def test_without_token_returns_401(self, client):
        r = client.post("/api/v1/account-holders/", json={})
        assert r.status_code == 401


class TestGetProfile:
    def test_get_profile_success(self, client, token1, holder1):
        r = client.get("/api/v1/account-holders/me", headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["first_name"] == "Alice"

    def test_get_profile_not_found(self, client, token1):
        r = client.get("/api/v1/account-holders/me", headers=auth(token1))
        assert r.status_code == 404


class TestUpdateProfile:
    def test_update_profile_success(self, client, token1, holder1):
        r = client.put("/api/v1/account-holders/me", json={"phone": "+19999999999"},
                       headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["phone"] == "+19999999999"
        assert r.json()["first_name"] == "Alice"  # unchanged

    def test_partial_update_preserves_other_fields(self, client, token1, holder1):
        r = client.put("/api/v1/account-holders/me",
                       json={"address": "99 New Addr, City, ST 00000"},
                       headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["last_name"] == "Smith"
