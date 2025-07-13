# app.py
import os
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, send_from_directory, flash
)
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_migrate import Migrate

from models import db, User, Ticket, Comment, Attachment

# ——— App setup ———
app = Flask(__name__)
app.secret_key = 'replace-with-your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File uploads
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ——— Update last_seen on each request ———
@app.before_request
def update_user_last_seen():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ——— Routes ———

@app.route('/')
@login_required
def dashboard():
    open_count = Ticket.query.filter_by(status='open').count()
    closed_count = Ticket.query.filter_by(status='closed').count()
    return render_template('dashboard.html',
                           open_count=open_count,
                           closed_count=closed_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = User(username=request.form['username'],
                 email=request.form['email'])
        u.set_password(request.form['password'])
        db.session.add(u)
        db.session.commit()
        flash('Registration successful – please log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/tickets')
@login_required
def ticket_list():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('tickets.html', tickets=tickets)

@app.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def ticket_new():
    if request.method == 'POST':
        t = Ticket(title=request.form['title'],
                   description=request.form['description'],
                   creator=current_user)
        db.session.add(t)
        db.session.commit()
        return redirect(url_for('ticket_list'))
    return render_template('new_ticket.html')

@app.route('/tickets/<int:tid>')
@login_required
def ticket_view(tid):
    t = Ticket.query.get_or_404(tid)
    return render_template('ticket.html', ticket=t)

@app.route('/tickets/<int:tid>/comment', methods=['POST'])
@login_required
def ticket_comment(tid):
    t = Ticket.query.get_or_404(tid)
    c = Comment(ticket_id=tid,
                author=current_user.username,
                body=request.form['body'])
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('ticket_view', tid=tid))

@app.route('/tickets/<int:tid>/attach', methods=['POST'])
@login_required
def ticket_attach(tid):
    t = Ticket.query.get_or_404(tid)
    file = request.files.get('attachment')
    if file and allowed_file(file.filename):
        fname = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        att = Attachment(ticket_id=tid, filename=fname)
        db.session.add(att)
        db.session.commit()
    return redirect(url_for('ticket_view', tid=tid))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
