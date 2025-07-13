# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    username       = db.Column(db.String(80), unique=True, nullable=False)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    password_hash  = db.Column(db.String(128), nullable=False)
    is_admin       = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, server_default=db.func.now())
    # NEW field to track activity
    last_seen      = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_online(self):
        """True if seen in the last 5 minutes."""
        return (datetime.utcnow() - self.last_seen).total_seconds() < 5 * 60

    def __repr__(self):
        return f'<User {self.username}>'


class Ticket(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    title         = db.Column(db.String(200), nullable=False)
    description   = db.Column(db.Text, nullable=False)
    status        = db.Column(db.String(20), default='open')
    created_at    = db.Column(db.DateTime, server_default=db.func.now())
    updated_at    = db.Column(db.DateTime, onupdate=db.func.now())
    creator_id    = db.Column(db.Integer, db.ForeignKey('user.id'))
    assignee_id   = db.Column(db.Integer, db.ForeignKey('user.id'))

    creator       = db.relationship('User', foreign_keys=[creator_id], backref='created_tickets')
    assignee      = db.relationship('User', foreign_keys=[assignee_id], backref='assigned_tickets')
    comments      = db.relationship('Comment', backref='ticket', cascade='all, delete-orphan')
    attachments   = db.relationship('Attachment', backref='ticket', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Ticket {self.title}>'


class Comment(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    ticket_id   = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    author      = db.Column(db.String(80), nullable=False)
    body        = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<Comment {self.id} on Ticket {self.ticket_id}>'


class Attachment(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    ticket_id    = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    filename     = db.Column(db.String(256), nullable=False)
    uploaded_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Attachment {self.filename}>'
