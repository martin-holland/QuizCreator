"""
Database models using SQLAlchemy with SQLite
SQLite is built into Python - no installation needed!
Easy to migrate to PostgreSQL/MySQL later by just changing the connection string.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

# ============================================================================
# Database Models
# ============================================================================

class Source(db.Model):
    """Source model - URLs, PDFs, Word docs, Images"""
    __tablename__ = 'sources'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 'url', 'pdf', 'word', 'image'
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Extracted text or URL
    meta_data = db.Column(db.Text)  # JSON string (renamed from 'metadata' - SQLAlchemy reserved word)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    topics = db.relationship('Topic', backref='source', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'metadata': json.loads(self.meta_data) if self.meta_data else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Topic(db.Model):
    """Topic model - represents a section/topic from a source"""
    __tablename__ = 'topics'
    
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='topic', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'title': self.title,
            'description': self.description or '',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Question(db.Model):
    """Question model"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    answers = db.Column(db.Text, nullable=False)  # JSON string of answers array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'question_text': self.question_text,
            'answers': json.loads(self.answers) if self.answers else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Quiz(db.Model):
    """Quiz model"""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    question_ids = db.Column(db.Text, nullable=False)  # JSON array of question IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'question_ids': json.loads(self.question_ids) if self.question_ids else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class QuizAttempt(db.Model):
    """Quiz attempt model"""
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    selected_answers = db.Column(db.Text, nullable=False)  # JSON object
    question_scores = db.Column(db.Text, nullable=False)  # JSON object
    total_score = db.Column(db.Float, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'selected_answers': json.loads(self.selected_answers) if self.selected_answers else {},
            'question_scores': json.loads(self.question_scores) if self.question_scores else {},
            'total_score': self.total_score,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

