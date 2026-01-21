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



admin_router = APIRouter(prefix="/admin", tags=["Admin"])

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@admin_router.put("/users/{user_id}", response_model=UserProfileSchema)
async def admin_update_user(
    user_id: int,
    update_data: AdminUpdateUserSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Админ может обновлять любого пользователя, включая роль.
    """
    # Проверка, что текущий пользователь — админ
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор может изменять роли"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    if update_data.email:
        user.email = update_data.email
    if update_data.username:
        user.username = update_data.username
    if update_data.password:
        user.password = pwd_context.hash(update_data.password)
    if update_data.role:
        user.role = update_data.role

    db.commit()
    db.refresh(user)

    # Статистика экзаменов
    passed_exams_count = db.query(func.count(Exam.id)).filter(
        Exam.user_id == user.id,
        Exam.status == ExamStatusChoices.completed
    ).scalar()

    avg_score_result = db.query(func.avg(Exam.score)).filter(
        Exam.user_id == user.id,
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