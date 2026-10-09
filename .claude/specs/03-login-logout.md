# Spec: Login and Logout

## Overview

Make the existing `/login` page functional and implement `/logout`, so a registered user can sign in, stay signed in across requests using Flask's built-in signed-cookie session, and sign out. Registration (Step 2) creates accounts but nothing can yet authenticate them; this step adds the session mechanism that profile and expense features (Steps 4+) will rely on to know who the current user is.

## Depends on

* Step 1 — Database setup (`users` table, `get_db()`)
* Step 2 — Registration (users with werkzeug-hashed passwords, `get_user_by_email()`)

## Routes

* `GET /login` — render the login form (already exists); if the user is already logged in, redirect to `/profile` — public
* `POST /login` — validate credentials, store the user id in the session and redirect to `/profile` on success; re-render the form with an error on failure — public
* `GET /logout` — clear the session and redirect to `/` (landing) — public (safe to call when not logged in)

(`/login` gains `methods=["GET", "POST"]`; `/logout` is converted from a stub string to a real route. `/profile` stays the Step 4 stub and is only used as a redirect target.)

## Database changes

No database changes. The existing `users` table and the `get_user_by_email()` helper from Step 2 are sufficient. Passwords are verified against `password_hash` with `check_password_hash`.

## Templates

* **Create:** none
* **Modify:**
  * `templates/login.html` — form `action` uses `{{ url_for('login') }}` instead of the hardcoded `/login`; re-populate the `email` field (never the password) after a failed attempt
  * `templates/base.html` — navbar is session-aware: logged-out users see "Sign in" and "Get started"; logged-in users see a "Sign out" link (`url_for('logout')`) instead

## Files to change

* `app.py` — set `app.secret_key`, import `session`, implement `POST /login` and `/logout`, make the navbar state available to templates
* `templates/login.html` — changes listed above
* `templates/base.html` — session-aware navbar
* `CLAUDE.md` — update the routes table: `/logout` and `POST /login` implemented

## Files to create

* `tests/test_login_logout.py` — pytest tests for the login/logout flow (temporary database, same lazy-import fixture pattern as `tests/test_registration.py`)

## New dependencies

No new dependencies. Use Flask's built-in `session`.

## Rules for implementation

* No SQLAlchemy or ORMs
* Parameterised queries only
* Passwords hashed with werkzeug; verify with `check_password_hash`, never compare plaintext
* Use CSS variables — never hardcode hex values
* All templates extend `base.html`
* `app.secret_key` is read from the `SECRET_KEY` environment variable with a clearly named development fallback; never commit a real secret
* Look the user up with `get_user_by_email()` (email normalised with `.strip().lower()`); add no DB logic to the route
* Failed login shows one generic message ("Invalid email or password.") whether the email is unknown or the password is wrong — do not reveal which; re-render with HTTP 200
* Empty email or password shows the same generic error (or "All fields are required.") and does not touch the session
* On success store only the integer `user_id` in `session` (no password hash, no name); call `session.clear()` before setting it to avoid keeping stale session data
* `/logout` must call `session.clear()` and redirect with `url_for('landing')`; do not use a raw string return
* Use `url_for()` for every link and redirect
* Do not implement `/profile` or any other stub route; do not add a "login required" decorator yet (that arrives with Step 4)
* Do not add new pip packages; keep port 5001 and all other routes unchanged

## Definition of done

* [x] `GET /login` renders the form with no error
* [x] Logging in as [`demo@spendly.com`](mailto:demo@spendly.com) / `demo123` redirects (302) to `/profile`
* [x] After login, the session contains `user_id` equal to the user's id and nothing sensitive
* [x] Email matching is case-insensitive and ignores surrounding whitespace (` `[`DEMO@Spendly.com`](mailto:DEMO@Spendly.com) works)
* [x] A wrong password shows "Invalid email or password." and sets no `user_id` in the session
* [x] An unknown email shows the same message as a wrong password
* [x] Empty or whitespace-only fields show an error and sets no session
* [x] After a failed attempt the email field keeps its value; the password field is empty
* [x] A user registered through `/register` can immediately log in with the same credentials
* [x] Visiting `/login` while logged in redirects to `/profile`
* [x] `GET /logout` clears the session and redirects (302) to `/`
* [x] `GET /logout` while logged out does not error and still redirects to `/`
* [x] Navbar shows "Sign in" / "Get started" when logged out, and "Sign out" (linking to `/logout`) when logged in
* [x] The login form's action is generated with `url_for('login')`; no hardcoded URLs in changed templates
* [x] `pytest` passes, including the new `tests/test_login_logout.py` and existing tests
* [x] App starts with `python app.py` on port 5001 with no errors