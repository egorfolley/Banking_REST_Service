"""Auth endpoint tests."""
import pytest
from tests.conftest import auth, signup_and_login, USER1, USER2


class TestSignup:
    def test_signup_returns_tokens(self, client):
        r = client.post("/api/v1/auth/signup", json={"email": "x@example.com", "password": "Secure1!"})
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_signup_duplicate_email(self, client, token1):
        r = client.post("/api/v1/auth/signup", json={"email": USER1[0], "password": USER1[1]})
        assert r.status_code == 400

    def test_signup_weak_no_upper(self, client):
        r = client.post("/api/v1/auth/signup", json={"email": "x@x.com", "password": "nouppercase1!"})
        assert r.status_code == 422

    def test_signup_weak_no_digit(self, client):
        r = client.post("/api/v1/auth/signup", json={"email": "x@x.com", "password": "NoDigitPass!"})
        assert r.status_code == 422

    def test_signup_weak_no_special(self, client):
        r = client.post("/api/v1/auth/signup", json={"email": "x@x.com", "password": "NoSpecial1"})
        assert r.status_code == 422

    def test_signup_too_short(self, client):
        r = client.post("/api/v1/auth/signup", json={"email": "x@x.com", "password": "Sh0!"})
        assert r.status_code == 422


class TestLogin:
    def test_login_success(self, client, token1):
        r = client.post("/api/v1/auth/login", json={"email": USER1[0], "password": USER1[1]})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client, token1):
        r = client.post("/api/v1/auth/login", json={"email": USER1[0], "password": "WrongPass1!"})
        assert r.status_code == 401

    def test_login_unknown_email(self, client):
        r = client.post("/api/v1/auth/login", json={"email": "nobody@x.com", "password": "Pass1!"})
        assert r.status_code == 401

    def test_login_same_error_for_wrong_email_and_wrong_password(self, client, token1):
        """Same error message prevents email enumeration."""
        r_bad_email = client.post("/api/v1/auth/login", json={"email": "ghost@x.com", "password": USER1[1]})
        r_bad_pass = client.post("/api/v1/auth/login", json={"email": USER1[0], "password": "WrongPass1!"})
        assert r_bad_email.status_code == r_bad_pass.status_code == 401
        assert r_bad_email.json()["detail"] == r_bad_pass.json()["detail"]


class TestTokens:
    def test_me_with_valid_token(self, client, token1):
        r = client.get("/api/v1/auth/me", headers=auth(token1))
        assert r.status_code == 200
        assert r.json()["user"]["email"] == USER1[0]

    def test_me_without_token_returns_401(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_me_with_bad_token_returns_401(self, client):
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage.token.here"})
        assert r.status_code == 401

    def test_refresh_token(self, client, token1):
        login = client.post("/api/v1/auth/login", json={"email": USER1[0], "password": USER1[1]}).json()
        r = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_refresh_with_access_token_rejected(self, client, token1):
        r = client.post("/api/v1/auth/refresh", json={"refresh_token": token1})
        assert r.status_code == 401
