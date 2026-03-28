from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Represents an authorized user and their associated profile metadata.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    profile_pic = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chats = db.relationship('Chat', backref='user', lazy=True, cascade="all, delete-orphan")

# Manages unique conversation sessions between a user and the AI.
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    is_starred = db.Column(db.Boolean, default=False, nullable=False)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade="all, delete-orphan")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Stores individual message entries for transparency and chat history retrieval.
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    sender = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
