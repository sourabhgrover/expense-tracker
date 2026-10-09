# Plan: Registration (Step 2)

Source spec: `.claude/specs/02-registration.md` (branch `feature/registration`). Plan only — no code written yet.

## Context
`/register` currently renders a form that posts to a GET-only route, so accounts cannot be created. Step 2 makes it work: validate input, store a werkzeug-hashed password in `users`, redirect to `/login`. It is the prerequisite for login/logout (Step 3). No sessions, no auto-login, no schema change, no new packages.

## Steps

### 1. `database/db.py` — add two helpers (after `seed_db`)
Follow the existing `conn = get_db(); try: ... finally: conn.close()` pattern; `generate_password_hash` is already imported.
- `get_user_by_email(email)` — `SELECT * FROM users WHERE email = ?`; returns `sqlite3.Row` or `None`. No normalisation inside; caller passes a normalised email.
- `create_user(name, email, password)` — `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)` with `generate_password_hash(password)`; commit; return `cursor.lastrowid`. Let `sqlite3.IntegrityError` propagate.

### 2. `app.py` — `/register` accepts GET and POST
- Imports: add `request, redirect, url_for` (flask), `import sqlite3`, and `get_user_by_email, create_user` (db).
- `@app.route("/register", methods=["GET", "POST"])`. GET unchanged.
- POST: read `name`/`email` stripped, email lowercased, password raw. Validate in this order, stop at first failure:
  1. any field empty/whitespace-only -> "All fields are required."
  2. email format (one `@`, non-empty local part, domain with an inner `.`, no whitespace) -> "Please enter a valid email address."
  3. `len(password) < 8` -> "Password must be at least 8 characters."
  4. `get_user_by_email(email)` exists -> "An account with that email already exists."
  5. `create_user(...)` inside `try/except sqlite3.IntegrityError` -> same duplicate message (race safety).
- Failure: `render_template("register.html", error=..., name=name, email=email)` with HTTP 200; never echo the password.
- Success: `redirect(url_for("login"))` (302). No session, no flash.
- Optional private `_validate_registration()` helper in `app.py` (no DB logic) to keep the route short.
- Leave all other stub routes and `/login` untouched.

### 3. `templates/register.html`
- `action="{{ url_for('register') }}"` (replaces hardcoded `/register`).
- `value="{{ name or '' }}"` on name, `value="{{ email or '' }}"` on email; none on password.
- `minlength="8"` on password. No CSS change (`.auth-error` already exists).

### 4. `tests/test_registration.py` (new)
- Fixture `client` (not named `app`, to avoid pytest-flask's hook): monkeypatch `db.DB_PATH` to `tmp_path/"test.db"`, call `db.init_db()` and `db.seed_db()`, then lazily `from app import app` inside the fixture (app.py runs init/seed at import, which would otherwise hit the real `expense_tracker.db`), set `TESTING`, yield `app.test_client()`.
- Reuse the `tmp_db` monkeypatch pattern from `tests/test_db.py`. If `from app import app` fails under bare `pytest`, add a minimal `pytest.ini` (`pythonpath = .`).
- Cases: GET renders form without error; valid POST -> 302 to `/login`; row created, hash != plaintext and `check_password_hash` passes; email stored lowercase/trimmed; duplicate `demo@spendly.com` and case/whitespace variant rejected with no new row; 7-char password; empty/whitespace-only fields (parametrised); invalid emails `abc`, `a@b`, `@x.com`, `a@.com`, `a@b.`, `a b@c.com` (parametrised); name/email retained and password absent after failure; form action is `/register`; forced `IntegrityError` race (patch `app.get_user_by_email` to return `None`) gives 200 + duplicate message, not 500; HTML-escaping of a `"><script>` name; no session cookie set on success.

## Risks / notes
- Import-time `init_db()/seed_db()` in `app.py` — handled by lazy import in the fixture.
- DB `UNIQUE` on email is case-sensitive, so normalisation in the route is mandatory.
- Passwords are not stripped (only the required check strips); hash is of the raw value.
- HTML `type=email`/`minlength` are browser-only; server validation is authoritative.
- Duplicate message reveals that an email exists (accepted by spec). No CSRF exists in the project; out of scope.

## Critical files
- `app.py`, `database/db.py`, `templates/register.html` (modify)
- `tests/test_registration.py` (create), `tests/test_db.py` (pattern reference)

## Verification
1. `pytest tests/test_registration.py -v`, then full `pytest` (confirm `test_db.py` still passes).
2. Confirm the real `expense_tracker.db` was not modified by the tests (mtime/user count before vs after).
3. `python app.py` starts on port 5001 without errors.
4. Browser pass: GET `/register`; short password keeps name/email and blanks password; `demo@spendly.com` shows duplicate error; valid new user redirects to `/login`; check the row via `sqlite3` (lowercase email, `scrypt:`/`pbkdf2:` hash).
5. Grep: no hardcoded `/register` in the template, no f-string SQL in `db.py`.
6. `git diff` touches only the files listed above (plus optional `pytest.ini`).
