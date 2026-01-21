from .database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Integer, DateTime, Enum, ForeignKey,
    Text, Boolean, Float
)
from typing import Optional, List
from datetime import datetime
from enum import Enum as PyEnum



class DifficultyChoices(str, PyEnum):
    easy = 'easy'
    medium = 'medium'
    advanced = 'advanced'


class ExamStatusChoices(str, PyEnum):
    in_progress = 'in_progress'
    completed = 'completed'
    failed = 'failed'


class RoleChoices(str, PyEnum):
    admin = 'admin'
    user = 'user'


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[RoleChoices] = mapped_column(Enum(RoleChoices), default=RoleChoices.admin)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user_token: Mapped[List['RefreshToken']] = relationship('RefreshToken', back_populates='user',
                                                            cascade='all, delete-orphan')
    user_exams: Mapped[List['Exam']] = relationship('Exam', back_populates='user', cascade='all, delete-orphan')
    user_favorites: Mapped[List['Favorite']] = relationship('Favorite', back_populates='user',
                                                            cascade='all, delete-orphan')
    user_comments: Mapped[List['Comment']] = relationship('Comment', back_populates='user',
                                                          cascade='all, delete-orphan')
    user_likes: Mapped[List['Like']] = relationship('Like', back_populates='user', cascade='all, delete-orphan')
    user_predictions: Mapped[List['AIPredictionLog']] = relationship('AIPredictionLog', back_populates='user',
                                                                     cascade='all, delete-orphan')


class RefreshToken(Base):
    __tablename__ = 'refresh_token'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped[User] = relationship(User, back_populates='user_token')
    token: Mapped[str] = mapped_column(String, nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = 'category'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    category_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    category_questions: Mapped[List['Question']] = relationship('Question', back_populates='category',
                                                                cascade='all, delete-orphan')


class Question(Base):
    __tablename__ = 'question'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[DifficultyChoices] = mapped_column(Enum(DifficultyChoices), default=DifficultyChoices.easy)
    category_id: Mapped[int] = mapped_column(ForeignKey('category.id'))
    category: Mapped[Category] = relationship(Category, back_populates='category_questions')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    question_options: Mapped[List['AnswerOption']] = relationship('AnswerOption', back_populates='question',
                                                                  cascade='all, delete-orphan')
    question_favorites: Mapped[List['Favorite']] = relationship('Favorite', back_populates='question',
                                                                cascade='all, delete-orphan')
    question_comments: Mapped[List['Comment']] = relationship('Comment', back_populates='question',
                                                              cascade='all, delete-orphan')
    question_likes: Mapped[List['Like']] = relationship('Like', back_populates='question', cascade='all, delete-orphan')
    exam_answers: Mapped[List['ExamAnswer']] = relationship('ExamAnswer', back_populates='question',
                                                            cascade='all, delete-orphan')


class AnswerOption(Base):
    __tablename__ = 'answer_option'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey('question.id'))
    question: Mapped[Question] = relationship(Question, back_populates='question_options')
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)


class Exam(Base):
    __tablename__ = 'exam'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped[User] = relationship(User, back_populates='user_exams')
    score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ExamStatusChoices] = mapped_column(Enum(ExamStatusChoices), default=ExamStatusChoices.in_progress)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    exam_answers: Mapped[List['ExamAnswer']] = relationship('ExamAnswer', back_populates='exam',
                                                            cascade='all, delete-orphan')


class ExamAnswer(Base):
    __tablename__ = 'exam_answer'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exam.id'))
    exam: Mapped[Exam] = relationship(Exam, back_populates='exam_answers')
    question_id: Mapped[int] = mapped_column(ForeignKey('question.id'))
    question: Mapped[Question] = relationship(Question, back_populates='exam_answers')
    selected_option_id: Mapped[int] = mapped_column(ForeignKey('answer_option.id'))
    selected_option: Mapped[AnswerOption] = relationship(AnswerOption)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Video(Base):
    __tablename__ = 'video'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    video_comments: Mapped[List['Comment']] = relationship('Comment', back_populates='video',
                                                           cascade='all, delete-orphan')
    video_likes: Mapped[List['Like']] = relationship('Like', back_populates='video', cascade='all, delete-orphan')


class Comment(Base):
    __tablename__ = 'comment'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped[User] = relationship(User, back_populates='user_comments')
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey('question.id'), nullable=True)
    question: Mapped[Optional[Question]] = relationship(Question, back_populates='question_comments')
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey('video.id'), nullable=True)
    video: Mapped[Optional[Video]] = relationship(Video, back_populates='video_comments')

    comment_likes: Mapped[List['Like']] = relationship('Like', back_populates='comment', cascade='all, delete-orphan')


class Like(Base):
    __tablename__ = 'like'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped[User] = relationship(User, back_populates='user_likes')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey('comment.id'), nullable=True)
    comment: Mapped[Optional[Comment]] = relationship(Comment, back_populates='comment_likes')
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey('video.id'), nullable=True)
    video: Mapped[Optional[Video]] = relationship(Video, back_populates='video_likes')
    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey('question.id'), nullable=True)
    question: Mapped[Optional[Question]] = relationship(Question, back_populates='question_likes')


class Favorite(Base):
    __tablename__ = 'favorite'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped[User] = relationship(User, back_populates='user_favorites')
    question_id: Mapped[int] = mapped_column(ForeignKey('question.id'))
    question: Mapped[Question] = relationship(Question, back_populates='question_favorites')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AIPredictionLog(Base):
    __tablename__ = 'ai_prediction_log'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped[User] = relationship(User, back_populates='user_predictions')
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    predicted_label: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PddModel(Base):
    __tablename__ = 'Pdd_model'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(32))  # новая колонка
    description: Mapped[str] = mapped_column(String(256))  # новая колонка
    images: Mapped[List[str]] = mapped_column(String)