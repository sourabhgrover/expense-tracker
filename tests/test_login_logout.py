import pytest

from database import db

DEMO = {"email": "demo@spendly.com", "password": "demo123"}
ERROR = b"Invalid email or password."


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    db.seed_db()
    # Imported lazily: app.py runs init_db()/seed_db() at import time, which
    # must hit the temporary database rather than the real one.
    from app import app

    app.config["TESTING"] = True
    return app.test_client()


def login(client, email=DEMO["email"], password=DEMO["password"]):
    return client.post("/login", data={"email": email, "password": password})


def session_uid(client):
    with client.session_transaction() as sess:
        return sess.get("user_id")


def test_get_login_renders_form(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b'action="/login"' in response.data
    assert b"auth-error" not in response.data


def test_demo_login_redirects_to_profile(client):
    response = login(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")


def test_session_holds_only_user_id(client):
    response = login(client)
    with client.session_transaction() as sess:
        assert sess["user_id"] == 1
        assert set(sess.keys()) <= {"user_id", "_permanent"}
    cookie = response.headers.get("Set-Cookie", "")
    assert DEMO["password"] not in cookie
    assert "scrypt" not in cookie and "pbkdf2" not in cookie


def test_email_is_trimmed_and_case_insensitive(client):
    response = login(client, email="  DEMO@Spendly.com ")
    assert response.status_code == 302
    assert session_uid(client) == 1


def test_wrong_password(client):
    response = login(client, password="nope-nope")
    assert response.status_code == 200
    assert ERROR in response.data
    assert session_uid(client) is None


def test_unknown_email_same_message(client):
    wrong_pw = login(client, password="nope-nope")
    unknown = login(client, email="ghost@example.com")
    assert unknown.status_code == 200
    assert ERROR in unknown.data
    assert ERROR in wrong_pw.data
    assert session_uid(client) is None


@pytest.mark.parametrize(
    "email,password",
    [("", ""), ("   ", "demo123"), ("demo@spendly.com", ""), ("demo@spendly.com", "   ")],
)
def test_empty_fields_rejected(client, email, password):
    response = login(client, email=email, password=password)
    assert response.status_code == 200
    assert b"auth-error" in response.data
    assert session_uid(client) is None


def test_email_repopulated_password_not(client):
    response = login(client, password="wrong-password")
    assert b'value="demo@spendly.com"' in response.data
    assert b"wrong-password" not in response.data


def test_email_is_html_escaped(client):
    response = login(client, email='"><script>x</script>@a.com')
    assert b"<script>x</script>" not in response.data


def test_registered_user_can_login(client):
    creds = {"name": "Asha Rao", "email": "asha.rao@example.com", "password": "password123"}
    assert client.post("/register", data=creds).status_code == 302
    response = login(client, creds["email"], creds["password"])
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    assert session_uid(client) is not None


def test_login_page_redirects_when_logged_in(client):
    login(client)
    response = client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")


def test_logout_clears_session_and_redirects(client):
    login(client)
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert session_uid(client) is None


def test_logout_when_logged_out(client):
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_navbar_logged_out(client):
    html = client.get("/").data
    assert b"Sign in" in html
    assert b"Get started" in html
    assert b"Sign out" not in html


def test_navbar_logged_in(client):
    login(client)
    html = client.get("/").data
    assert b"Sign out" in html
    assert b'href="/logout"' in html
    assert b"Get started" not in html


def test_login_replaces_stale_session(client):
    with client.session_transaction() as sess:
        sess["junk"] = "stale"
    login(client)
    with client.session_transaction() as sess:
        assert "junk" not in sess
        assert sess["user_id"] == 1
