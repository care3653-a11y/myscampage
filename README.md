# MyScamShield

A free, confidential support platform for scam victims. It helps people report
what happened, understand the warning signs, and get guided to the right
authorities by trained volunteers.

**Principles baked into this project**
- No payment is ever collected. There is no payment code or dependency.
- The self-check is a transparent checklist, not AI and not a verdict.
- Volunteers support and guide — they do not recover funds and never ask for money.
- Every path points people to real, official reporting channels.

## Run locally

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then edit .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # put into SECRET_KEY

python app.py
```

Visit http://127.0.0.1:5000

If you don't set `ADMIN_PASSWORD`, a temporary one is printed in the console at
startup. Sign in at `/admin/login`.

## Configuration

All configuration is via environment variables — see `.env.example`.
`SECRET_KEY`, `DATABASE_URL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FLASK_DEBUG`.

## Live chat

The volunteer live-chat widget uses Tawk.to. Replace the property ID in
`templates/base.html` with your own before going live.

## Deploy

Use a production server, e.g.:

```bash
gunicorn app:app
```

Set `SECRET_KEY`, `ADMIN_PASSWORD`, and a real `DATABASE_URL` in the environment,
and keep `FLASK_DEBUG=0`.

## Project layout

```
app.py                 Flask app: routes, models, auth
requirements.txt       Dependencies (no payment libraries)
.env.example           Config template
templates/             Jinja2 templates
static/images/         Logo and imagery
```
