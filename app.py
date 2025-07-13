import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Ticket, Comment, Attachment
from flask_migrate import Migrate
from datetime import datetime

# Configuration
app = Flask(__name__)
app.secret_key = 'replace-with-secure-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Uploads
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXT = {'png','jpg','jpeg','gif','pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(fname):
    return '.' in fname and fname.rsplit('.',1)[1].lower() in ALLOWED_EXT

# Extensions
db.init_app(app)
Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('ticket_list'))

@app.route('/users')
@login_required
def user_list():
    users = User.query.order_by(User.created_at).all()
    return render_template('users.html', users=users)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already taken','danger')
        else:
            u = User(username=request.form['username'])
            u.set_password(request.form['password'])
            db.session.add(u)
            db.session.commit()
            login_user(u)
            return redirect(url_for('ticket_list'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and u.check_password(request.form['password']):
            login_user(u)
            return redirect(url_for('ticket_list'))
        flash('Invalid credentials','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('ticket_list'))

@app.route('/tickets')
def ticket_list():
    q = request.args.get('q','')
    query = Ticket.query
    if q:
        query = query.filter(Ticket.title.ilike(f'%{q}%'))
    tickets = query.order_by(Ticket.ticket_number.desc()).all()
    return render_template('tickets.html', tickets=tickets, q=q)

@app.route('/tickets/new', methods=['GET','POST'])
def ticket_new():
    if request.method == 'POST':
        last = Ticket.query.order_by(Ticket.ticket_number.desc()).first()
        next_num = last.ticket_number + 1 if last else 1
        name_input = request.form.get('submitted_by','').strip()
        if current_user.is_authenticated:
            submitter = current_user.username
        elif name_input:
            submitter = name_input
        else:
            submitter = f"anon{next_num}"
        t = Ticket(ticket_number=next_num, submitted_by=submitter,
                   title=request.form['title'], description=request.form['description'])
        db.session.add(t)
        db.session.commit()
        file = request.files.get('attachment')
        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            db.session.add(Attachment(ticket_id=t.id, filename=fname))
            db.session.commit()
        return redirect(url_for('ticket_list'))
    return render_template('new_ticket.html')

@app.route('/tickets/<int:tid>')
def ticket_view(tid):
    return render_template('ticket.html', ticket=Ticket.query.get_or_404(tid))

@app.route('/tickets/<int:tid>/comment', methods=['POST'])
@login_required
def ticket_comment(tid):
    t = Ticket.query.get_or_404(tid)
    c = Comment(ticket=t, author=request.form['author'], body=request.form['body'])
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('ticket_view', tid=tid))

@app.route('/tickets/<int:tid>/status', methods=['POST'])
@login_required
def ticket_status(tid):
    t = Ticket.query.get_or_404(tid)
    t.status = request.form['status']
    t.finished_at = datetime.utcnow() if t.status.lower() == 'closed' else None
    db.session.commit()
    return redirect(url_for('ticket_view', tid=tid))

@app.route('/dashboard')
def dashboard():
    total = Ticket.query.count()
    open_count = Ticket.query.filter_by(status='Open').count()
    closed_count = Ticket.query.filter_by(status='Closed').count()
    avg_time = db.session.query(
        db.func.avg(
            db.func.julianday(Ticket.finished_at)
            - db.func.julianday(Ticket.created_at)
        )
    ).filter(Ticket.finished_at.isnot(None)).scalar()
    return render_template('dashboard.html', total=total, open_count=open_count, closed_count=closed_count, avg_time=avg_time)

@app.route('/tickets/<int:tid>/upload', methods=['POST'])
@login_required
def upload_attachment(tid):
    t = Ticket.query.get_or_404(tid)
    file = request.files.get('attachment')
    if file and allowed_file(file.filename):
        fname = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        db.session.add(Attachment(ticket_id=tid, filename=fname))
        db.session.commit()
    return redirect(url_for('ticket_view', tid=tid))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)