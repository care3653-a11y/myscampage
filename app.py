from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'myscamshield-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myscamshield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ====================== MODELS ======================
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    scam_type = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Open")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), nullable=False)
    sender = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def generate_ticket_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ====================== ROUTES ======================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        scam_type = request.form.get('scam_type')
        description = request.form.get('description')

        ticket_id = generate_ticket_id()

        new_ticket = Ticket(
            ticket_id=ticket_id,
            name=name,
            email=email,
            scam_type=scam_type,
            description=description
        )
        db.session.add(new_ticket)
        db.session.commit()

        welcome = Message(
            ticket_id=ticket_id,
            sender="admin",
            message="Thank you for reaching out. Our team has received your report."
        )
        db.session.add(welcome)
        db.session.commit()

        flash('Report Successfully Submitted! A representative will contact you soon via email or phone.', 'success')
        return redirect('/report')  # Stay on report page

    return render_template('report.html')

@app.route('/detector')
def detector():
    return render_template('detector.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

# Admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == "admin" and request.form.get('password') == "123456":
            session['admin_logged_in'] = True
            flash('Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid login', 'danger')
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please login first', 'danger')
        return redirect(url_for('admin_login'))
    tickets = Ticket.query.order_by(Ticket.date.desc()).all()
    return render_template('admin.html', tickets=tickets)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🚀 MyScamShield is running at http://127.0.0.1:5000")
    app.run(debug=True)