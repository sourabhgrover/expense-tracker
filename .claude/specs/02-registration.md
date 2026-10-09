# Spec: Registration

## Overview
Make the existing `/register` page functional so a visitor can create a Spendly account. The form submits name, email and password; the server validates them, stores a hashed password in the `users` table and redirects to the login page. This is the first user-facing write path and is required before login/logout (Step 3) can authenticate anyone.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`, `init_db()`)

## Routes
- `GET /register` — render the registration form (already exists, unchanged behaviour) — public
- `POST /register` — validate input, create the user, redirect to `/login` on success; re-render the form with an error on failure — public

(Same URL, so `register` gains `methods=["GET", "POST"]`; no new URL paths.)

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`) is sufficient. Two new helper functions are added to `database/db.py`:
- `get_user_by_email(email)` — returns a `sqlite3.Row` or `None`
- `create_user(name, email, password)` — hashes the password with werkzeug, inserts the row, returns the new user id; raises `sqlite3.IntegrityError` on duplicate email

## Templates
- **Create:** none
- **Modify:** `templates/register.html`
  - Form `action` uses `{{ url_for('register') }}` instead of the hardcoded `/register`
  - Re-populate the `name` and `email` fields (never the password) with submitted values after a validation error
  - Add `minlength="8"` to the password input

## Files to change
- `app.py` — accept POST on `/register`, add validation and call DB helpers, import `request`, `redirect`, `url_for`
- `database/db.py` — add `get_user_by_email()` and `create_user()`
- `templates/register.html` — changes listed above

## Files to create
- `tests/test_registration.py` — pytest tests for the registration flow (uses a temporary database)

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders, no f-strings in SQL)
- Passwords hashed with werkzeug (`generate_password_hash`); never store or log plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All DB logic lives in `database/db.py`; the route only reads the form, validates, calls helpers and renders/redirects
- Use `url_for()` for every internal link and redirect
- Do not implement any stub route (`/login` POST, `/logout`, `/profile`, etc.); do not start a session or log the user in — that is Step 3
- Validation (server-side, in this order): name, email and password all required after stripping whitespace; email must contain `@` and a `.` in the domain part; password at least 8 characters; email not already registered
- Normalise email with `.strip().lower()` before lookup and insert
- Duplicate email: check with `get_user_by_email()` and also catch `sqlite3.IntegrityError` to cover races; show a generic message such as "An account with that email already exists"
- Validation failures re-render `register.html` with the `error` variable and HTTP 200 (the template already renders `error`)
- Always close DB connections (`try/finally`), consistent with existing `db.py` helpers
- Keep port 5001 and existing routes unchanged

## Definition of done
- [ ] `GET /register` still renders the form with no errors
- [ ] Submitting valid name, new email and an 8+ character password redirects (302) to `/login`
- [ ] The new row exists in `users` and `password_hash` is a werkzeug hash, not the plaintext password
- [ ] Email is stored lowercase and trimmed (`  Foo@Example.COM ` is saved as `foo@example.com`)
- [ ] Submitting an email that is already registered (including `demo@spendly.com`) shows an error on the form and creates no new row
- [ ] Submitting a password shorter than 8 characters shows an error and creates no row
- [ ] Submitting with any field empty or whitespace-only shows an error and creates no row
- [ ] Submitting an invalid email (e.g. `abc`) shows an error and creates no row
- [ ] After a failed submission the name and email fields keep their values; the password field is empty
- [ ] The form's action is generated with `url_for('register')`; no hardcoded URLs in the template
- [ ] `pytest tests/test_registration.py` passes
- [ ] App starts with `python app.py` on port 5001 with no errors
