"""
Migration script to move data from JSON to SQLite database
Run this once to migrate existing data: python migrate_to_sqlite.py
"""
from app import create_app
from app.database import db, Source, Topic, Question, Quiz, QuizAttempt
import json
import os

def migrate_json_to_sqlite():
    """Migrate data from JSON file to SQLite database"""
    app = create_app()
    
    with app.app_context():
        # Check if JSON file exists
        json_file = 'data/quiz_data.json'
        if not os.path.exists(json_file):
            print("No JSON file found. Starting fresh with SQLite database.")
            return
        
        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("Migrating data from JSON to SQLite...")
        
        # Migrate sources
        sources_count = 0
        for source_data in data.get('sources', []):
            source = Source(
                id=source_data.get('id'),
                type=source_data.get('type'),
                title=source_data.get('title'),
                content=source_data.get('content'),
                meta_data=json.dumps(source_data.get('metadata', {}))
            )
            db.session.merge(source)  # Use merge to handle existing IDs
            sources_count += 1
        print(f"  Migrated {sources_count} sources")
        
        # Migrate topics
        topics_count = 0
        for topic_data in data.get('topics', []):
            topic = Topic(
                id=topic_data.get('id'),
                source_id=topic_data.get('source_id'),
                title=topic_data.get('title'),
                description=topic_data.get('description', '')
            )
            db.session.merge(topic)
            topics_count += 1
        print(f"  Migrated {topics_count} topics")
        
        # Migrate questions
        questions_count = 0
        for question_data in data.get('questions', []):
            question = Question(
                id=question_data.get('id'),
                topic_id=question_data.get('topic_id'),
                question_text=question_data.get('question_text'),
                answers=json.dumps(question_data.get('answers', []))
            )
            db.session.merge(question)
            questions_count += 1
        print(f"  Migrated {questions_count} questions")
        
        # Migrate quizzes
        quizzes_count = 0
        for quiz_data in data.get('quizzes', []):
            quiz = Quiz(
                id=quiz_data.get('id'),
                title=quiz_data.get('title'),
                description=quiz_data.get('description', ''),
                question_ids=json.dumps(quiz_data.get('question_ids', []))
            )
            db.session.merge(quiz)
            quizzes_count += 1
        print(f"  Migrated {quizzes_count} quizzes")
        
        # Migrate quiz attempts
        attempts_count = 0
        for attempt_data in data.get('quiz_attempts', []):
            attempt = QuizAttempt(
                id=attempt_data.get('id'),
                quiz_id=attempt_data.get('quiz_id'),
                selected_answers=json.dumps(attempt_data.get('selected_answers', {})),
                question_scores=json.dumps(attempt_data.get('question_scores', {})),
                total_score=attempt_data.get('total_score', 0.0)
            )
            db.session.merge(attempt)
            attempts_count += 1
        print(f"  Migrated {attempts_count} quiz attempts")
        
        db.session.commit()
        print("\n✅ Migration complete!")
        print(f"Total: {sources_count} sources, {topics_count} topics, {questions_count} questions, {quizzes_count} quizzes, {attempts_count} attempts")
        print("\nNote: JSON file is kept as backup. You can delete it after verifying the migration.")

if __name__ == '__main__':
    migrate_json_to_sqlite()

