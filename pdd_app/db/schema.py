from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum



class DifficultyChoices(str, Enum):
    easy = 'easy'
    medium = 'medium'
    advanced = 'advanced'


class ExamStatusChoices(str, Enum):
    in_progress = 'in_progress'
    completed = 'completed'
    failed = 'failed'


class RoleChoices(str, Enum):
    admin = 'admin'
    user = 'user'



class UserCreateSchema(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserSchema(BaseModel):
    id: int
    email: str
    username: str
    role: RoleChoices
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatusSchema(BaseModel):
    passed_exams: int
    avg_score: float


class UserProfileSchema(BaseModel):
    id: int
    email: str
    username: str
    status: UserStatusSchema

    class Config:
        from_attributes = True


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserUpdateSchema(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=6)

class AdminUpdateUserSchema(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[RoleChoices] = None

class UserRegisterResponseSchema(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True



class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class AccessTokenSchema(BaseModel):
    access_token: str


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str


class LogoutResponseSchema(BaseModel):
    message: str



class RefreshTokenSchema(BaseModel):
    id: int
    user_id: int
    token: str
    created_date: datetime

    class Config:
        from_attributes = True



class CategoryCreateSchema(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=100)


class CategoryUpdateSchema(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=100)


class CategorySchema(BaseModel):
    id: int
    category_name: str

    class Config:
        from_attributes = True



class AnswerOptionCreateSchema(BaseModel):
    text: str
    is_correct: bool = False


class AnswerOptionSchema(BaseModel):
    id: int
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class AnswerOptionResponseSchema(BaseModel):
    id: str
    text: str

    class Config:
        from_attributes = True



class QuestionCreateSchema(BaseModel):
    text: str
    image: Optional[str] = None
    explanation: str
    difficulty: DifficultyChoices = DifficultyChoices.easy
    category_id: int
    options: List[AnswerOptionCreateSchema]

    @validator('options')
    def validate_options(cls, v):
        if len(v) < 2:
            raise ValueError('Вопрос должен содержать минимум 2 варианта ответа')
        correct_count = sum(1 for option in v if option.is_correct)
        if correct_count != 1:
            raise ValueError('Должен быть только один правильный ответ')
        return v


class QuestionUpdateSchema(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[DifficultyChoices] = None
    category_id: Optional[int] = None


class QuestionOptionSchema(BaseModel):
    id: str
    text: str

    class Config:
        from_attributes = True


class QuestionSchema(BaseModel):
    id: str
    text: str
    image: Optional[str]
    options: List[QuestionOptionSchema]

    class Config:
        from_attributes = True


class QuestionDetailSchema(BaseModel):
    id: str
    text: str
    explanation: str
    correct_option_id: str

    class Config:
        from_attributes = True


class QuestionListResponseSchema(BaseModel):
    items: List[QuestionSchema]


class QuestionAdminSchema(BaseModel):
    id: int
    text: str
    image: Optional[str]
    explanation: str
    difficulty: DifficultyChoices
    category_id: int
    created_at: datetime
    options: List[AnswerOptionSchema]

    class Config:
        from_attributes = True



class ExamStartRequestSchema(BaseModel):
    user_id: int


class ExamSchema(BaseModel):
    id: int
    user_id: int
    score: int
    status: ExamStatusChoices
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExamStartResponseSchema(BaseModel):
    message: str
    exam_id: int
    started_at: datetime
    questions: List[QuestionSchema]  # 20 случайных вопросов


class ExamAnswerRequestSchema(BaseModel):
    question_id: int
    option_id: int


class ExamAnswerResponseSchema(BaseModel):
    message: str
    is_correct: bool
    current_score: int


class ExamFinishResponseSchema(BaseModel):
    message: str
    exam_id: int
    score: int
    total_questions: int
    passed: bool  # Прошел ли экзамен (например, >= 18 правильных из 20)
    finished_at: datetime



class ExamAnswerSchema(BaseModel):
    id: int
    exam_id: int
    question_id: int
    selected_option_id: int
    is_correct: bool
    answered_at: datetime

    class Config:
        from_attributes = True



class VideoCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    url: str


class VideoUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    url: Optional[str] = None


class VideoSchema(BaseModel):
    id: int
    title: str
    description: str
    url: str
    views_count: int
    created_at: datetime

    class Config:
        from_attributes = True



class CommentCreateSchema(BaseModel):
    text: str = Field(..., min_length=1)
    question_id: Optional[int] = None
    video_id: Optional[int] = None

    @validator('video_id')
    def validate_target(cls, v, values):
        question_id = values.get('question_id')
        if question_id is None and v is None:
            raise ValueError('Необходимо указать question_id или video_id')
        if question_id is not None and v is not None:
            raise ValueError('Можно указать только question_id или video_id, но не оба')
        return v


class CommentUpdateSchema(BaseModel):
    text: str = Field(..., min_length=1)


class CommentSchema(BaseModel):
    id: int
    user_id: int
    text: str
    created_at: datetime
    question_id: Optional[int]
    video_id: Optional[int]
    likes_count: int = 0

    class Config:
        from_attributes = True



class LikeCreateSchema(BaseModel):
    comment_id: Optional[int] = None
    video_id: Optional[int] = None
    question_id: Optional[int] = None

    @validator('question_id')
    def validate_target(cls, v, values):
        comment_id = values.get('comment_id')
        video_id = values.get('video_id')
        targets = [comment_id, video_id, v]
        if sum(x is not None for x in targets) != 1:
            raise ValueError('Необходимо указать только один из: comment_id, video_id или question_id')
        return v


class LikeSchema(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    comment_id: Optional[int]
    video_id: Optional[int]
    question_id: Optional[int]

    class Config:
        from_attributes = True


class LikeResponseSchema(BaseModel):
    status: str
    likes_count: int



class FavoriteCreateSchema(BaseModel):
    question_id: int


class FavoriteSchema(BaseModel):
    id: int
    user_id: int
    question_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FavoriteResponseSchema(BaseModel):
    status: str


class FavoriteQuestionSchema(BaseModel):
    id: int
    question: QuestionSchema
    created_at: datetime

    class Config:
        from_attributes = True



class AIPredictionRequestSchema(BaseModel):
    pass


class AIPredictionResponseSchema(BaseModel):
    label: str
    category: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class AIPredictionLogSchema(BaseModel):
    id: int
    user_id: int
    image_url: str
    predicted_label: str
    category: str
    description: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True



class PddModelCreateSchema(BaseModel):
    name: str = Field(..., max_length=32)
    category: str = Field(..., max_length=32)
    description: str = Field(..., max_length=256)
    images: str


class PddModelUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=32)
    category: Optional[str] = Field(None, max_length=32)
    description: Optional[str] = Field(None, max_length=256)
    images: Optional[str] = None


class PddModelSchema(BaseModel):
    id: int
    name: str
    category: str
    description: str
    images: str

    class Config:
        from_attributes = True



class ErrorSchema(BaseModel):
    detail: str


class ValidationErrorSchema(BaseModel):
    detail: str