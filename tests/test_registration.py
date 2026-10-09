import pytest
from werkzeug.security import check_password_hash

from database import db

VALID = {"name": "Asha Rao", "email": "asha.rao@example.com", "password": "password123"}


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


def user_count():
    conn = db.get_db()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


def post(client, **overrides):
    return client.post("/register", data={**VALID, **overrides})


def test_get_renders_form_without_error(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b'action="/register"' in response.data
    assert b"auth-error" not in response.data


def test_valid_post_redirects_to_login(client):
    response = post(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_valid_post_creates_user_with_hashed_password(client):
    before = user_count()
    post(client)
    assert user_count() == before + 1
    row = db.get_user_by_email(VALID["email"])
    assert row["name"] == VALID["name"]
    assert row["password_hash"] != VALID["password"]
    assert check_password_hash(row["password_hash"], VALID["password"])


def test_email_is_trimmed_and_lowercased(client):
    post(client, email="  Foo@Example.COM ")
    assert db.get_user_by_email("foo@example.com") is not None


@pytest.mark.parametrize("email", ["demo@spendly.com", " DEMO@Spendly.com "])
def test_duplicate_email_rejected(client, email):
    before = user_count()
    response = post(client, email=email)
    assert response.status_code == 200
    assert b"already exists" in response.data
    assert user_count() == before


def test_short_password_rejected(client):
    before = user_count()
    response = post(client, password="short12")
    assert response.status_code == 200
    assert b"at least 8 characters" in response.data
    assert user_count() == before


@pytest.mark.parametrize("field", ["name", "email", "password"])
@pytest.mark.parametrize("value", ["", "   "])
def test_empty_fields_rejected(client, field, value):
    before = user_count()
    response = post(client, **{field: value})
    assert response.status_code == 200
    assert b"auth-error" in response.data
    assert user_count() == before


@pytest.mark.parametrize(
    "email", ["abc", "a@b", "@x.com", "a@.com", "a@b.", "a b@c.com", "a@@b.com"]
)
def test_invalid_email_rejected(client, email):
    before = user_count()
    response = post(client, email=email)
    assert response.status_code == 200
    assert b"valid email" in response.data
    assert user_count() == before


def test_fields_repopulated_but_not_password(client):
    response = post(client, password="short")
    assert b'value="Asha Rao"' in response.data
    assert b'value="asha.rao@example.com"' in response.data
    assert b"short" not in response.data.replace(b"at least 8 characters", b"")


def test_name_is_html_escaped(client):
    response = post(client, name='"><script>x</script>', password="short")
    assert b"<script>x</script>" not in response.data


def test_integrity_error_race_shows_duplicate_message(client, monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "get_user_by_email", lambda email: None)
    before = user_count()
    response = post(client, email="demo@spendly.com")
    assert response.status_code == 200
    assert b"already exists" in response.data
    assert user_count() == before


def test_success_does_not_set_session_cookie(client):
    response = post(client)
    assert "Set-Cookie" not in response.headers
