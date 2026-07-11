"""
MyScamShield — a support and guidance platform for scam victims.

What this app does, honestly:
  - Lets people report a scam and receive a reference number.
  - Offers a guided red-flag self-check (a transparent checklist, NOT AI and
    NOT a verdict) that always points people to real reporting authorities.
  - Connects people to trained volunteers who listen and guide them to the
    right channels. Volunteers do not recover funds and never ask for money.

There is no payment collection anywhere in this project by design.
"""

import os
import secrets
import string
import random
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
app = Flask(__name__)

# SECRET_KEY must come from the environment in production. If it is missing we
# generate a random one so the app still runs locally, but sessions will reset
# on restart — the printed warning makes that explicit.
_secret = os.getenv("SECRET_KEY")
if not _secret:
    _secret = secrets.token_urlsafe(32)
    print("[MyScamShield] WARNING: SECRET_KEY not set. Using a temporary "
          "random key. Set SECRET_KEY in the environment for production.")
app.config["SECRET_KEY"] = _secret

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///myscamshield.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# --------------------------------------------------------------------------- #
# Admin credentials
#   - Username from ADMIN_USERNAME (defaults to "admin").
#   - Password is read from ADMIN_PASSWORD and hashed in memory at startup.
#   - If no password is set, a strong random one is generated and printed once,
#     so there is never a weak hard-coded default.
# --------------------------------------------------------------------------- #
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
_admin_pw = os.getenv("ADMIN_PASSWORD")
if not _admin_pw:
    _admin_pw = secrets.token_urlsafe(12)
    print(f"[MyScamShield] No ADMIN_PASSWORD set. Temporary admin password "
          f"for this session: {_admin_pw}")
ADMIN_PASSWORD_HASH = generate_password_hash(_admin_pw)


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(40))            # now actually stored
    scam_type = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Open")


class Note(db.Model):
    """Internal volunteer notes on a ticket (admin-side only)."""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), nullable=False)
    author = db.Column(db.String(40), nullable=False, default="volunteer")
    body = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


def generate_ticket_id():
    """Short human-friendly reference, e.g. MSS-7F3K9A2Q."""
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"MSS-{code}"


def admin_required():
    return bool(session.get("admin_logged_in"))


# --------------------------------------------------------------------------- #
# Public routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/self-check")
def self_check():
    return render_template("selfcheck.html")


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        scam_type = (request.form.get("scam_type") or "").strip()
        description = (request.form.get("description") or "").strip()

        if not name or not email or not description:
            flash("Please fill in your name, email, and what happened.", "danger")
            return render_template("report.html")

        ticket_id = generate_ticket_id()
        db.session.add(Ticket(
            ticket_id=ticket_id,
            name=name,
            email=email,
            phone=phone or None,
            scam_type=scam_type or None,
            description=description,
        ))
        db.session.commit()
        return redirect(url_for("report_success", ticket_id=ticket_id))

    return render_template("report.html")


@app.route("/report/success/<ticket_id>")
def report_success(ticket_id):
    ticket = Ticket.query.filter_by(ticket_id=ticket_id).first_or_404()
    return render_template("report_success.html", ticket=ticket)


@app.route("/support")
def support():
    return render_template("support.html")


@app.route("/resources")
def resources():
    return render_template("resources.html")


# --------------------------------------------------------------------------- #
# Admin routes
# --------------------------------------------------------------------------- #
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin_logged_in"] = True
            flash("Signed in.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect username or password.", "danger")
    return render_template("admin_login.html")


@app.route("/admin")
def admin_dashboard():
    if not admin_required():
        flash("Please sign in first.", "danger")
        return redirect(url_for("admin_login"))
    tickets = Ticket.query.order_by(Ticket.date.desc()).all()
    return render_template("admin.html", tickets=tickets)


@app.route("/admin/ticket/<ticket_id>", methods=["GET", "POST"])
def admin_ticket(ticket_id):
    if not admin_required():
        flash("Please sign in first.", "danger")
        return redirect(url_for("admin_login"))

    ticket = Ticket.query.filter_by(ticket_id=ticket_id).first_or_404()

    if request.method == "POST":
        new_status = request.form.get("status")
        note_body = (request.form.get("note") or "").strip()
        if new_status in {"Open", "In progress", "Closed"}:
            ticket.status = new_status
        if note_body:
            db.session.add(Note(ticket_id=ticket_id, body=note_body))
        db.session.commit()
        flash("Ticket updated.", "success")
        return redirect(url_for("admin_ticket", ticket_id=ticket_id))

    notes = Note.query.filter_by(ticket_id=ticket_id).order_by(Note.date.asc()).all()
    return render_template("admin_ticket.html", ticket=ticket, notes=notes)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Signed out.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("MyScamShield running at http://127.0.0.1:5000")
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
