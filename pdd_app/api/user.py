from fastapi import HTTPException, Depends, APIRouter, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pdd_app.db.models import User, Exam, ExamStatusChoices
from ..db.schema import UserProfileSchema, UserStatusSchema, AdminUpdateUserSchema, UserUpdateSchema
from passlib.context import CryptContext
from ..db.database import SessionLocal
from .auth import get_current_user

user_router = APIRouter(prefix='/users', tags=['Users'])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@user_router.get('/me', response_model=UserProfileSchema)
async def get_current_user_profile(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить профиль текущего пользователя

    Возвращает информацию о пользователе и его статистику по экзаменам
    """
    # Получаем статистику экзаменов
    passed_exams_count = db.query(func.count(Exam.id)).filter(
        Exam.user_id == current_user.id,
        Exam.status == ExamStatusChoices.completed
    ).scalar()

    # Средний балл
    avg_score_result = db.query(func.avg(Exam.score)).filter(
        Exam.user_id == current_user.id,
        Exam.status == ExamStatusChoices.completed
    ).scalar()

    avg_score = float(avg_score_result) if avg_score_result else 0.0

    stats = UserStatusSchema(
        passed_exams=passed_exams_count or 0,
        avg_score=round(avg_score, 2)
    )

    return UserProfileSchema(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        stats=stats
    )


@user_router.get('/{user_id}', response_model=UserProfileSchema)
async def get_user_profile(
        user_id: int,
        db: Session = Depends(get_db)
):
    """
    Получить профиль пользователя по ID

    - **user_id**: ID пользователя
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )

    # Получаем статистику экзаменов
    passed_exams_count = db.query(func.count(Exam.id)).filter(
        Exam.user_id == user_id,
        Exam.status == ExamStatusChoices.completed
    ).scalar()

    avg_score_result = db.query(func.avg(Exam.score)).filter(
        Exam.user_id == user_id,
        Exam.status == ExamStatusChoices.completed
    ).scalar()

    avg_score = float(avg_score_result) if avg_score_result else 0.0

    stats = UserStatusSchema(
        passed_exams=passed_exams_count or 0,
        avg_score=round(avg_score, 2)
    )

    return UserProfileSchema(
        id=user.id,
        email=user.email,
        username=user.username,
        stats=stats
    )




@user_router.put("/me", response_model=UserProfileSchema)
async def update_current_user_profile(
    update_data: UserUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Обновление профиля текущего пользователя:
    - email
    - username
    - пароль
    """
    if not any([update_data.email, update_data.username, update_data.password]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать хотя бы одно поле для обновления",
        )

    if update_data.email:
        current_user.email = update_data.email
    if update_data.username:
        current_user.username = update_data.username
    if update_data.password:
        current_user.password = pwd_context.hash(update_data.password)

    db.commit()
    db.refresh(current_user)

    # Обновляем статистику
    passed_exams_count = db.query(func.count(Exam.id)).filter(
        Exam.user_id == current_user.id,
        Exam.status == ExamStatusChoices.completed
    ).scalar()

    avg_score_result = db.query(func.avg(Exam.score)).filter(
        Exam.user_id == current_user.id,
        Exam.status == ExamStatusChoices.completed
    ).scalar()

    avg_score = float(avg_score_result) if avg_score_result else 0.0

    stats = UserStatusSchema(
        passed_exams=passed_exams_count or 0,
        avg_score=round(avg_score, 2)
    )

    return UserProfileSchema(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        stats=stats
    )