# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Spendly is a Flask-based expense tracker built incrementally as a step-by-step learning project. Many routes and modules are intentionally left as stubs with comments like `# Students will write this file in Step 1 — Database Setup` or return placeholder text such as `"Logout — coming in Step 3"`. When working on this codebase, check whether the piece you're touching is one of these placeholders before assuming it's a bug — implement it according to the step it references rather than deleting the scaffold comments.

## Commands

```bash
# Activate the virtualenv (already created under venv/)
venv\Scripts\activate          # PowerShell/cmd
source venv/Scripts/activate   # Git Bash

# Install dependencies
pip install -r requirements.txt

# Run the dev server (debug mode, port 5001)
python app.py

# Run tests (pytest + pytest-flask are in requirements.txt; no tests/ directory exists yet)
pytest
pytest path/to/test_file.py::test_name   # single test
```

There is no lint/format tooling configured in this repo.

## Architecture

- **`app.py`** — single Flask entrypoint. All routes are defined directly on the module-level `app` object (no blueprints). Routes are grouped into two sections via comments: implemented page routes (`/`, `/register`, `/login`, `/terms`, `/privacy`) and placeholder routes for not-yet-built features (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`), each returning a plain string naming the future step that implements it.
- **`database/db.py`** — intended to hold `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample data for development). Not yet implemented — currently just a comment describing the contract. The SQLite file itself (`expense_tracker.db`) is gitignored and created at runtime, not committed.
- **`templates/`** — Jinja2 templates. `base.html` defines the shared shell (nav, footer, `main.js` include) with `{% block title %}`, `{% block head %}`, `{% block content %}`, and `{% block scripts %}`. Page templates (`landing.html`, `register.html`, `login.html`, `terms.html`, `privacy.html`) extend `base.html` and pull in their own page-specific stylesheet/script via the `head`/`scripts` blocks (e.g. `landing.html` loads `css/landing.css` and references `js/landing.js`'s DOM ids).
- **`static/css/`** — `style.css` holds shared/base styles used across all pages; per-page styles (e.g. `landing.css`) live in their own file and are only loaded by the page that needs them.
- **`static/js/`** — `main.js` is loaded globally from `base.html` (currently empty, meant to grow as shared features are added); per-page scripts (e.g. `landing.js`) are loaded only from the page's own `{% block scripts %}` and should stay vanilla JS with no dependencies/frameworks, consistent with the existing `landing.js` modal implementation.

## Conventions to follow

- No JS framework or external JS libraries — keep all client-side code vanilla JS, matching `static/js/landing.js`.
- When adding a new page, follow the existing template pattern: extend `base.html`, add a page-specific CSS/JS file under `static/` only if the page needs one, and wire the route in `app.py`.
