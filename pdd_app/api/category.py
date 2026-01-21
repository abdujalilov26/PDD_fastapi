from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from pdd_app.db.models import Category, User, RoleChoices
from ..db.schema import CategoryCreateSchema, CategoryUpdateSchema, CategorySchema
from ..db.database import SessionLocal
from .auth import get_current_user

category_router = APIRouter(prefix='/categories', tags=['Categories'])


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


@category_router.post('/', status_code=status.HTTP_201_CREATED, response_model=CategorySchema)
async def create_category(
        category_data: CategoryCreateSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Создать новую категорию (только для администраторов)

    - **category_name**: Название категории
    """
    check_admin_role(current_user)

    # Проверяем уникальность
    existing = db.query(Category).filter(Category.category_name == category_data.category_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Категория с таким названием уже существует'
        )

    new_category = Category(
        category_name=category_data.category_name
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


@category_router.get('/', response_model=List[CategorySchema])
async def get_categories(
        limit: int = 20,
        offset: int = 0,
        db: Session = Depends(get_db)
):
    """
    Получить список категорий

    - **limit**: Количество результатов
    - **offset**: Смещение для пагинации
    """
    categories = db.query(Category).order_by(Category.id.asc()).offset(offset).limit(limit).all()
    return categories


@category_router.get('/{category_id}', response_model=CategorySchema)
async def get_category_detail(
        category_id: int,
        db: Session = Depends(get_db)
):
    """
    Получить детальную информацию о категории

    - **category_id**: ID категории
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Категория не найдена'
        )
    return category


@category_router.put('/{category_id}', response_model=CategorySchema)
async def update_category(
        category_id: int,
        category_data: CategoryUpdateSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Обновить категорию (только для администраторов)

    - **category_id**: ID категории
    - **category_name**: Новое название категории
    """
    check_admin_role(current_user)

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Категория не найдена'
        )

    # Проверка уникальности нового названия
    if category_data.category_name:
        existing = db.query(Category).filter(
            Category.category_name == category_data.category_name,
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Категория с таким названием уже существует'
            )
        category.category_name = category_data.category_name

    db.commit()
    db.refresh(category)
    return category


@category_router.delete('/{category_id}', status_code=status.HTTP_200_OK)
async def delete_category(
        category_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Удалить категорию (только для администраторов)

    - **category_id**: ID категории
    """
    check_admin_role(current_user)

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Категория не найдена'
        )

    db.delete(category)
    db.commit()

    return {"message": "Категория успешно удалена", "category_id": category_id}