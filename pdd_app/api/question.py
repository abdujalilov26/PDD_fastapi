from fastapi import HTTPException, Depends, APIRouter, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from pdd_app.db.models import (
    Question, AnswerOption, Category,
    DifficultyChoices, User, RoleChoices
)
from ..db.schema import (
    QuestionCreateSchema, QuestionUpdateSchema, QuestionAdminSchema,
    AnswerOptionSchema, CategorySchema
)
from ..db.database import SessionLocal
from .auth import get_current_user

question_router = APIRouter(prefix='/questions', tags=['Questions'])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_admin_role(current_user: User):
    """Проверка прав администратора"""
    if current_user.role != RoleChoices.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Доступ запрещен. Требуются права администратора.'
        )


@question_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_question(
        question_data: QuestionCreateSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Создать новый вопрос (только для администраторов)

    - **text**: Текст вопроса
    - **explanation**: Объяснение правильного ответа
    - **difficulty**: Уровень сложности (easy, medium, advanced)
    - **category_id**: ID категории
    - **image**: URL изображения (опционально)
    - **options**: Список вариантов ответов (минимум 2, только 1 правильный)
    """
    # Проверяем права администратора
    check_admin_role(current_user)

    # Проверяем существование категории
    category = db.query(Category).filter(Category.id == question_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Категория не найдена'
        )

    # Валидация вариантов ответов уже происходит в QuestionCreateSchema validator

    # Создаем новый вопрос
    new_question = Question(
        text=question_data.text,
        image=question_data.image,
        explanation=question_data.explanation,
        difficulty=question_data.difficulty,
        category_id=question_data.category_id,
        created_at=datetime.utcnow()
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    # Создаем варианты ответов
    for option_data in question_data.options:
        answer_option = AnswerOption(
            question_id=new_question.id,
            text=option_data.text,
            is_correct=option_data.is_correct
        )
        db.add(answer_option)

    db.commit()
    db.refresh(new_question)

    return {
        'message': 'Вопрос успешно создан',
        'question_id': new_question.id
    }


@question_router.get('/', response_model=List[QuestionAdminSchema])
async def get_questions(
        category_id: Optional[int] = None,
        difficulty: Optional[DifficultyChoices] = None,
        limit: int = 20,
        offset: int = 0,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить список вопросов с фильтрацией

    - **category_id**: Фильтр по категории
    - **difficulty**: Фильтр по сложности (easy, medium, advanced)
    - **limit**: Количество результатов
    - **offset**: Смещение для пагинации
    """
    query = db.query(Question)

    if category_id:
        query = query.filter(Question.category_id == category_id)

    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    questions = query.order_by(Question.created_at.desc()).offset(offset).limit(limit).all()

    return questions


@question_router.get('/{question_id}', response_model=QuestionAdminSchema)
async def get_question_detail(
        question_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить детальную информацию о вопросе

    - **question_id**: ID вопроса
    """
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Вопрос не найден'
        )

    return question


@question_router.put('/{question_id}')
async def update_question(
        question_id: int,
        question_data: QuestionUpdateSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Обновить существующий вопрос (только для администраторов)

    - **question_id**: ID вопроса
    - Все поля опциональны, обновляются только переданные поля
    - Варианты ответов не обновляются через этот endpoint
    """
    # Проверяем права администратора
    check_admin_role(current_user)

    # Проверяем существование вопроса
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Вопрос не найден'
        )

    # Если обновляется категория, проверяем её существование
    if question_data.category_id:
        category = db.query(Category).filter(Category.id == question_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Категория не найдена'
            )

    # Обновляем поля вопроса
    update_data = question_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)

    return {
        'message': 'Вопрос успешно обновлен',
        'question_id': question.id
    }


@question_router.delete('/{question_id}', status_code=status.HTTP_200_OK)
async def delete_question(
        question_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Удалить вопрос (только для администраторов)

    - **question_id**: ID вопроса
    """
    # Проверяем права администратора
    check_admin_role(current_user)

    # Проверяем существование вопроса
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Вопрос не найден'
        )

    db.delete(question)
    db.commit()

    return {
        'message': 'Вопрос успешно удален',
        'question_id': question_id
    }