from fastapi import HTTPException, Depends, APIRouter, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import random
from pdd_app.db.models import (
    Exam, ExamAnswer, Question, AnswerOption,
    ExamStatusChoices, User
)
from ..db.schema import (
    ExamSchema, ExamStartResponseSchema, ExamAnswerRequestSchema,
    ExamAnswerResponseSchema, ExamFinishResponseSchema,
    QuestionSchema, QuestionOptionSchema
)
from ..db.database import SessionLocal
from .auth import get_current_user

exam_router = APIRouter(prefix='/exams', tags=['Exams'])

# Константы для экзамена
EXAM_QUESTIONS_COUNT = 20
PASSING_SCORE = 18  # Минимум правильных ответов для прохождения


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@exam_router.post('/start', response_model=ExamStartResponseSchema, status_code=status.HTTP_201_CREATED)
async def start_exam(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Начать новый экзамен

    - Создает новый экзамен для пользователя
    - Выбирает 20 случайных вопросов
    - Возвращает ID экзамена и список вопросов
    """
    # Проверяем, есть ли у пользователя незавершенный экзамен
    existing_exam = db.query(Exam).filter(
        Exam.user_id == current_user.id,
        Exam.status == ExamStatusChoices.in_progress
    ).first()

    if existing_exam:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='У вас уже есть активный экзамен. Завершите его перед началом нового.'
        )

    # Получаем все вопросы
    all_questions = db.query(Question).all()

    if len(all_questions) < EXAM_QUESTIONS_COUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Недостаточно вопросов для экзамена. Требуется минимум {EXAM_QUESTIONS_COUNT} вопросов.'
        )

    # Выбираем 20 случайных вопросов
    selected_questions = random.sample(all_questions, EXAM_QUESTIONS_COUNT)

    # Создаем новый экзамен
    new_exam = Exam(
        user_id=current_user.id,
        status=ExamStatusChoices.in_progress,
        started_at=datetime.utcnow(),
        score=0
    )

    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)

    # Формируем список вопросов для ответа
    questions_response = []
    for question in selected_questions:
        questions_response.append(QuestionSchema(
            id=str(question.id),
            text=question.text,
            image=question.image,
            options=[
                QuestionOptionSchema(id=str(opt.id), text=opt.text)
                for opt in question.question_options
            ]
        ))

    return ExamStartResponseSchema(
        message='Экзамен начат',
        exam_id=new_exam.id,
        started_at=new_exam.started_at,
        questions=questions_response
    )


@exam_router.post('/{exam_id}/answer', response_model=ExamAnswerResponseSchema)
async def answer_question(
        exam_id: int,
        answer_data: ExamAnswerRequestSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Ответить на вопрос экзамена

    - **exam_id**: ID экзамена
    - **question_id**: ID вопроса
    - **option_id**: ID выбранного варианта ответа
    """
    # Проверяем существование экзамена
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Экзамен не найден'
        )

    # Проверяем что экзамен принадлежит текущему пользователю
    if exam.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Это не ваш экзамен'
        )

    # Проверяем статус экзамена
    if exam.status != ExamStatusChoices.in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Экзамен уже завершен'
        )

    # Проверяем существование вопроса
    question = db.query(Question).filter(Question.id == answer_data.question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Вопрос не найден'
        )

    # Проверяем существование варианта ответа
    option = db.query(AnswerOption).filter(
        AnswerOption.id == answer_data.option_id,
        AnswerOption.question_id == answer_data.question_id
    ).first()
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Вариант ответа не найден или не принадлежит этому вопросу'
        )

    # Проверяем, не отвечал ли пользователь на этот вопрос ранее
    existing_answer = db.query(ExamAnswer).filter(
        ExamAnswer.exam_id == exam_id,
        ExamAnswer.question_id == answer_data.question_id
    ).first()

    if existing_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Вы уже ответили на этот вопрос'
        )

    # Проверяем правильность ответа
    is_correct = option.is_correct

    # Сохраняем ответ
    exam_answer = ExamAnswer(
        exam_id=exam_id,
        question_id=answer_data.question_id,
        selected_option_id=answer_data.option_id,
        is_correct=is_correct,
        answered_at=datetime.utcnow()
    )

    db.add(exam_answer)

    # Обновляем счет если ответ правильный
    if is_correct:
        exam.score += 1

    db.commit()

    return ExamAnswerResponseSchema(
        message='Ответ сохранен',
        is_correct=is_correct,
        current_score=exam.score
    )


@exam_router.post('/{exam_id}/finish', response_model=ExamFinishResponseSchema)
async def finish_exam(
        exam_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Завершить экзамен

    - **exam_id**: ID экзамена

    Подсчитывает результат и определяет, прошел ли пользователь экзамен
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Экзамен не найден'
        )

    # Проверяем что экзамен принадлежит текущему пользователю
    if exam.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Это не ваш экзамен'
        )

    if exam.status != ExamStatusChoices.in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Экзамен уже завершен'
        )

    # Подсчитываем результаты
    total_questions = len(exam.exam_answers)

    # Проверяем, ответил ли пользователь на все вопросы
    if total_questions < EXAM_QUESTIONS_COUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Вы ответили только на {total_questions} из {EXAM_QUESTIONS_COUNT} вопросов'
        )

    # Определяем прошел ли экзамен
    passed = exam.score >= PASSING_SCORE

    # Завершаем экзамен
    exam.status = ExamStatusChoices.completed if passed else ExamStatusChoices.failed
    exam.finished_at = datetime.utcnow()

    db.commit()
    db.refresh(exam)

    return ExamFinishResponseSchema(
        message='Экзамен завершен',
        exam_id=exam.id,
        score=exam.score,
        total_questions=total_questions,
        passed=passed,
        finished_at=exam.finished_at
    )


@exam_router.get('/', response_model=List[ExamSchema])
async def get_user_exams(
        status: Optional[ExamStatusChoices] = None,
        limit: int = 20,
        offset: int = 0,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить историю экзаменов текущего пользователя

    - **status**: Фильтр по статусу (in_progress, completed, failed)
    - **limit**: Количество результатов
    - **offset**: Смещение для пагинации
    """
    query = db.query(Exam).filter(Exam.user_id == current_user.id)

    if status:
        query = query.filter(Exam.status == status)

    exams = query.order_by(Exam.started_at.desc()).offset(offset).limit(limit).all()

    return exams


@exam_router.get('/{exam_id}', response_model=ExamSchema)
async def get_exam_detail(
        exam_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить детальную информацию об экзамене

    - **exam_id**: ID экзамена
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Экзамен не найден'
        )

    # Проверяем что экзамен принадлежит текущему пользователю
    if exam.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Это не ваш экзамен'
        )

    return exam