from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at    = db.Column(db.DateTime, server_default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Ticket(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.Integer, unique=True, nullable=False)
    submitted_by  = db.Column(db.String(80), nullable=False)
    title         = db.Column(db.String(120), nullable=False)
    description   = db.Column(db.Text, nullable=False)
    status        = db.Column(db.String(20), default='Open', nullable=False)
    created_at    = db.Column(db.DateTime, server_default=db.func.now())
    updated_at    = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    finished_at   = db.Column(db.DateTime, nullable=True)
    comments      = db.relationship('Comment', backref='ticket', cascade='all, delete-orphan')
    attachments   = db.relationship('Attachment', backref='ticket', cascade='all, delete-orphan')

class Comment(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    ticket_id   = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    author      = db.Column(db.String(80), nullable=False)
    body        = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

class Attachment(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    ticket_id   = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    filename    = db.Column(db.String(256), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)