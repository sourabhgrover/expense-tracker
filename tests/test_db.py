import re
import sqlite3
from datetime import date

import pytest
from werkzeug.security import check_password_hash

from database import db

CATEGORIES = {
    "Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other",
}


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    return db


def test_tables_exist(tmp_db):
    conn = tmp_db.get_db()
    names = {
        r["name"]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"users", "expenses"} <= names
    user_cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)")}
    expense_cols = {r["name"] for r in conn.execute("PRAGMA table_info(expenses)")}
    conn.close()
    assert user_cols == {"id", "name", "email", "password_hash", "created_at"}
    assert expense_cols == {
        "id", "user_id", "amount", "category", "date", "description", "created_at",
    }


def test_get_db_row_factory_and_fk(tmp_db):
    conn = tmp_db.get_db()
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                 ("A", "a@x.com", "h"))
    row = conn.execute("SELECT * FROM users").fetchone()
    conn.close()
    assert row["name"] == "A"


def test_init_db_idempotent(tmp_db):
    tmp_db.init_db()
    tmp_db.init_db()


def test_seed_data(tmp_db):
    tmp_db.seed_db()
    conn = tmp_db.get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    expenses = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()

    assert len(users) == 1
    assert users[0]["email"] == "demo@spendly.com"
    assert users[0]["password_hash"] != "demo123"
    assert check_password_hash(users[0]["password_hash"], "demo123")

    assert len(expenses) == 8
    assert {e["category"] for e in expenses} == CATEGORIES
    prefix = date.today().strftime("%Y-%m-")
    for e in expenses:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["date"])
        assert e["date"].startswith(prefix)
        assert isinstance(e["amount"], float)
        assert e["user_id"] == users[0]["id"]


def test_seed_not_duplicated(tmp_db):
    tmp_db.seed_db()
    tmp_db.seed_db()
    conn = tmp_db.get_db()
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 8
    conn.close()


def test_foreign_key_enforced(tmp_db):
    conn = tmp_db.get_db()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (9999, 1.0, "Food", "2026-01-01"),
        )
    conn.close()


def test_duplicate_email_rejected(tmp_db):
    conn = tmp_db.get_db()
    conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                 ("A", "dup@x.com", "h"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                     ("B", "dup@x.com", "h"))
    conn.close()
