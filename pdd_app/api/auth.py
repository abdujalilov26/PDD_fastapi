from fastapi import (
    HTTPException, Depends, APIRouter, status
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

from pdd_app.db.models import User, RefreshToken, RoleChoices
from pdd_app.db.schema import (
    UserCreateSchema, UserLoginSchema, TokenSchema,
    UserRegisterResponseSchema, RefreshTokenRequestSchema,
    AccessTokenSchema, LogoutResponseSchema
)
from pdd_app.db.database import SessionLocal
from pdd_app.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)


# ================= SECURITY =================

security = HTTPBearer()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# ================= DB =================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================= PASSWORD =================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ================= JWT =================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")


# ================= REGISTER =================

@auth_router.post(
    "/register",
    response_model=UserRegisterResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreateSchema,
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(409, "Email already exists")

    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(409, "Username already exists")

    user = User(
        email=user_data.email,
        username=user_data.username,
        password=hash_password(user_data.password),
        role=RoleChoices.user,
        created_at=datetime.utcnow()
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ================= LOGIN =================

@auth_router.post("/login", response_model=TokenSchema)
async def login(
    login_data: UserLoginSchema,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(401, "Неверный email или пароль")

    access_token = create_access_token(
        {"sub": str(user.id), "email": user.email}
    )
    refresh_token = create_refresh_token(
        {"sub": str(user.id)}
    )

    db.add(RefreshToken(
        user_id=user.id,
        token=refresh_token,
        created_date=datetime.utcnow()
    ))
    db.commit()

    return TokenSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer"
    )


# ================= REFRESH =================

@auth_router.post("/refresh", response_model=AccessTokenSchema)
async def refresh_token(
    data: RefreshTokenRequestSchema,
    db: Session = Depends(get_db)
):
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(401, "Неверный тип токена")

    user_id = int(payload["sub"])

    token_in_db = db.query(RefreshToken).filter(
        RefreshToken.token == data.refresh_token,
        RefreshToken.user_id == user_id
    ).first()

    if not token_in_db:
        raise HTTPException(401, "Токен отозван")

    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "Пользователь не найден")

    return AccessTokenSchema(
        access_token=create_access_token(
            {"sub": str(user.id), "email": user.email}
        )
    )


# ================= LOGOUT =================

@auth_router.post("/logout", response_model=LogoutResponseSchema)
async def logout(
    data: RefreshTokenRequestSchema,
    db: Session = Depends(get_db)
):
    token = db.query(RefreshToken).filter(
        RefreshToken.token == data.refresh_token
    ).first()

    if token:
        db.delete(token)
        db.commit()

    return {"message": "Logout success"}


# ================= CURRENT USER =================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(401, "Неверный тип токена")

    user = db.query(User).get(int(payload["sub"]))
    if not user:
        raise HTTPException(404, "Пользователь не найден")

    return user


# ================= ADMIN =================

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != RoleChoices.admin:
        raise HTTPException(403, "Доступ запрещен")
    return current_user