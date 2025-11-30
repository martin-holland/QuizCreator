"""
Data models for Quiz Application - using SQLAlchemy with SQLite
SQLite is built into Python - no installation needed!
"""
from typing import List, Dict, Optional
from datetime import datetime
import json
from app.database import db, Source, Topic, Question, Quiz, QuizAttempt

# ============================================================================
# Source Model Functions
# ============================================================================

def create_source(source_type: str, title: str, content: str, metadata: Optional[Dict] = None) -> Dict:
    """Create a new source (URL, PDF, Word, Image)"""
    source = Source(
        type=source_type,
        title=title,
        content=content,
        meta_data=json.dumps(metadata) if metadata else None
    )
    db.session.add(source)
    db.session.commit()
    return source.to_dict()

def get_all_sources() -> List[Dict]:
    """Get all sources"""
    sources = Source.query.all()
    return [source.to_dict() for source in sources]

def get_source_by_id(source_id: int) -> Optional[Dict]:
    """Get source by ID"""
    source = Source.query.get(source_id)
    return source.to_dict() if source else None

def delete_source(source_id: int) -> bool:
    """Delete a source"""
    source = Source.query.get(source_id)
    if source:
        db.session.delete(source)
        db.session.commit()
        return True
    return False

# ============================================================================
# Topic Model Functions
# ============================================================================

def create_topic(source_id: int, title: str, description: Optional[str] = None) -> Dict:
    """Create a topic/section for a source"""
    topic = Topic(
        source_id=source_id,
        title=title,
        description=description or ''
    )
    db.session.add(topic)
    db.session.commit()
    return topic.to_dict()

def get_all_topics() -> List[Dict]:
    """Get all topics"""
    topics = Topic.query.all()
    return [topic.to_dict() for topic in topics]

def get_topic_by_id(topic_id: int) -> Optional[Dict]:
    """Get topic by ID"""
    topic = Topic.query.get(topic_id)
    return topic.to_dict() if topic else None

def get_topics_by_source(source_id: int) -> List[Dict]:
    """Get all topics for a source"""
    topics = Topic.query.filter_by(source_id=source_id).all()
    return [topic.to_dict() for topic in topics]

def update_topic(topic_id: int, title: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict]:
    """Update a topic"""
    topic = Topic.query.get(topic_id)
    if topic:
        if title is not None:
            topic.title = title
        if description is not None:
            topic.description = description
        db.session.commit()
        return topic.to_dict()
    return None

def delete_topic(topic_id: int) -> bool:
    """Delete a topic"""
    topic = Topic.query.get(topic_id)
    if topic:
        db.session.delete(topic)
        db.session.commit()
        return True
    return False

# ============================================================================
# Question Model Functions
# ============================================================================

def create_question(topic_id: int, question_text: str, answers: List[Dict]) -> Dict:
    """
    Create a question with answers
    answers: List of {text: str, is_correct: bool, points: float, id: int}
    """
    question = Question(
        topic_id=topic_id,
        question_text=question_text,
        answers=json.dumps(answers)
    )
    db.session.add(question)
    db.session.commit()
    return question.to_dict()

def get_all_questions() -> List[Dict]:
    """Get all questions"""
    questions = Question.query.all()
    return [question.to_dict() for question in questions]

def get_question_by_id(question_id: int) -> Optional[Dict]:
    """Get question by ID"""
    question = Question.query.get(question_id)
    return question.to_dict() if question else None

def get_questions_by_topic(topic_id: int) -> List[Dict]:
    """Get all questions for a topic"""
    questions = Question.query.filter_by(topic_id=topic_id).all()
    return [question.to_dict() for question in questions]

def delete_question(question_id: int) -> bool:
    """Delete a question"""
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
        return True
    return False

# ============================================================================
# Quiz Model Functions
# ============================================================================

def create_quiz(title: str, description: Optional[str], question_ids: List[int]) -> Dict:
    """Create a quiz from question IDs"""
    quiz = Quiz(
        title=title,
        description=description or '',
        question_ids=json.dumps(question_ids)
    )
    db.session.add(quiz)
    db.session.commit()
    return quiz.to_dict()

def get_all_quizzes() -> List[Dict]:
    """Get all quizzes"""
    quizzes = Quiz.query.all()
    return [quiz.to_dict() for quiz in quizzes]

def get_quiz_by_id(quiz_id: int) -> Optional[Dict]:
    """Get quiz by ID"""
    quiz = Quiz.query.get(quiz_id)
    return quiz.to_dict() if quiz else None

def delete_quiz(quiz_id: int) -> bool:
    """Delete a quiz"""
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        db.session.delete(quiz)
        db.session.commit()
        return True
    return False

def get_quiz_with_questions(quiz_id: int) -> Optional[Dict]:
    """Get quiz with full question data"""
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return None
    
    quiz_dict = quiz.to_dict()
    question_ids = json.loads(quiz.question_ids) if quiz.question_ids else []
    
    questions = []
    for qid in question_ids:
        question = Question.query.get(qid)
        if question:
            questions.append(question.to_dict())
    
    quiz_dict['questions'] = questions
    return quiz_dict

# ============================================================================
# Quiz Attempt Model Functions
# ============================================================================

def create_quiz_attempt(quiz_id: int, selected_answers: Dict[int, List[int]]) -> Dict:
    """
    Create a quiz attempt
    selected_answers: {question_id: [answer_ids]}
    """
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return None
    
    # Calculate score
    total_score = 0.0
    question_scores = {}
    
    question_ids = json.loads(quiz.question_ids) if quiz.question_ids else []
    
    for question_id, answer_ids in selected_answers.items():
        question = Question.query.get(question_id)
        if not question:
            continue
        
        question_score = 0.0
        answers = json.loads(question.answers) if question.answers else []
        
        for answer_id in answer_ids:
            answer = next((a for a in answers if a.get('id') == answer_id), None)
            if answer:
                question_score += answer.get('points', 0.0)
        
        # Apply minimum score of 0
        question_score = max(0.0, question_score)
        question_scores[question_id] = question_score
        total_score += question_score
    
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        selected_answers=json.dumps(selected_answers),
        question_scores=json.dumps(question_scores),
        total_score=total_score
    )
    db.session.add(attempt)
    db.session.commit()
    return attempt.to_dict()

def get_all_quiz_attempts() -> List[Dict]:
    """Get all quiz attempts"""
    attempts = QuizAttempt.query.all()
    return [attempt.to_dict() for attempt in attempts]

def get_quiz_attempt_by_id(attempt_id: int) -> Optional[Dict]:
    """Get quiz attempt by ID"""
    attempt = QuizAttempt.query.get(attempt_id)
    return attempt.to_dict() if attempt else None

def get_quiz_attempts_by_quiz(quiz_id: int) -> List[Dict]:
    """Get all attempts for a quiz"""
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).all()
    quiz = Quiz.query.get(quiz_id)
    quiz_dict = quiz.to_dict() if quiz else None
    
    result = []
    for attempt in attempts:
        attempt_dict = attempt.to_dict()
        if quiz_dict:
            attempt_dict['quiz'] = quiz_dict
        result.append(attempt_dict)
    
    return result

def get_quiz_attempt_with_details(attempt_id: int) -> Optional[Dict]:
    """Get quiz attempt with full question/answer details"""
    attempt = QuizAttempt.query.get(attempt_id)
    if not attempt:
        return None
    
    attempt_dict = attempt.to_dict()
    
    quiz = Quiz.query.get(attempt.quiz_id)
    if quiz:
        quiz_dict = get_quiz_with_questions(quiz.id)
        attempt_dict['quiz'] = quiz_dict
    
    # Add answer details
    selected_answers = json.loads(attempt.selected_answers) if attempt.selected_answers else {}
    question_scores = json.loads(attempt.question_scores) if attempt.question_scores else {}
    
    answer_details = {}
    for question_id, answer_ids in selected_answers.items():
        question = Question.query.get(question_id)
        if question:
            answer_details[question_id] = {
                'question': question.to_dict(),
                'selected_answer_ids': answer_ids,
                'score': question_scores.get(question_id, 0.0)
            }
    
    attempt_dict['answer_details'] = answer_details
    return attempt_dict
