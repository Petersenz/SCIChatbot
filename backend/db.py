from pathlib import Path
import os, datetime
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    BigInteger, Numeric, Enum,
    ForeignKey,
    Table,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


class UserRole(TypeDecorator):
    impl = Enum('a', 's', name='user_role')
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return {'admin': 'a', 'staff': 's'}.get(value, value)

    def process_result_value(self, value, dialect):
        return {'a': 'admin', 's': 'staff'}.get(value, value)


PRIMARY_NAMES = {'users': 'user_id', 'general': 'info_id', 'news': 'news_id',
                 'majors': 'major_id', 'curricula': 'curriculum_id',
                 'careers': 'career_id', 'intents': 'intent_id', 'chats': 'chat_id'}


def now():
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column('user_id', BigInteger, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    fullname = Column(String(255), nullable=False)
    role = Column(UserRole(), nullable=False, default='staff', server_default='s')
    email = Column(String(255), default="")
    tel_no = Column(String(20), default="")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now)


class Auth(Base):
    __tablename__ = "auth_sessions"
    token = Column(String(64), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    expires = Column(DateTime(timezone=True))


class MajorUser(Base):
    __tablename__ = "major_user"
    major_id = Column(
        BigInteger, ForeignKey("majors.major_id", ondelete="CASCADE"), primary_key=True
    )
    user_id = Column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )


class CurriculumCareer(Base):
    __tablename__ = "curriculum_career"
    curriculum_id = Column(
        BigInteger, ForeignKey("curricula.curriculum_id", ondelete="CASCADE"), primary_key=True
    )
    career_id = Column(
        BigInteger, ForeignKey("careers.career_id", ondelete="CASCADE"), primary_key=True
    )


SPECS = {
    "majors": {
        "major_name_th": String(255),
        "major_name_en": String(255),
        "description": Text,
        "tel": String(20),
        "email": String(255),
        "facebook_page": String(255),
        "website_url": String(255),
    },
    "general": {"topic": String(255), "description": Text, "image_url": Text},
    "news": {
        "title": String(255),
        "content": Text,
        "cover_image": Text,
        "views_count": Integer,
    },
    "curricula": {
        "degree_name": String(255),
        "curriculum_year": Integer,
        "description": Text,
        "total_credits": Integer,
        "tuition_fee": Numeric(10, 2),
        "file_url": Text,
    },
    "careers": {
        "job_title": String(255),
        "job_description": Text,
        "work_sector": Enum('g', 'p', 'o', 's', 'n', name='work_sector'),
        "salary_start": Numeric(10, 2),
        "skill_required": Text,
    },
    "intents": {
        "intent_name": String(255),
        "description": String(500),
        "prompt_context": Text,
        "action_type": String(50),
        "static_response": Text,
        "is_active": Boolean,
    },
}
MODELS = {"users": User}
for name, fields in SPECS.items():
    attrs = {
        "__tablename__": name,
        "id": Column(PRIMARY_NAMES[name], BigInteger, primary_key=True),
        "created_at": Column(DateTime(timezone=True), default=now),
        "updated_at": Column(DateTime(timezone=True), default=now, onupdate=now),
        "source_url": Column(Text, default=""),
    }
    attrs.update({k: Column(v, nullable=True) for k, v in fields.items()})
    if name == 'news':
        attrs['views_count'] = Column(Integer, default=0, server_default='0', nullable=False)
    if name in ("news", "curricula", "careers"):
        attrs["user_id"] = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"))
    if name == "curricula":
        attrs["major_id"] = Column(
            BigInteger, ForeignKey("majors.major_id", ondelete="RESTRICT"), nullable=False
        )
    MODELS[name] = type(name.title(), (Base,), attrs)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String(36), primary_key=True)
    owner = Column(String(64), index=True)
    title = Column(String(120))
    rating = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=now)
    rated_at = Column(DateTime(timezone=True))


class Chat(Base):
    __tablename__ = "chats"
    id = Column('chat_id', BigInteger, primary_key=True)
    session_id = Column(
        String(255), ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    user_query = Column(Text)
    bot_response = Column(Text)
    is_answered = Column(Boolean)
    is_helpful = Column(Boolean)
    response_time_ms = Column(Integer)
    timestamp = Column(DateTime(timezone=True), default=now)
    intent_id = Column(BigInteger, ForeignKey("intents.intent_id", ondelete="SET NULL"))
    sources = Column(JSONB, default=list)
    answer_mode = Column(String(30))
    resolved = Column(Boolean, default=False)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True)
    title = Column(Text)
    content = Column(Text)
    sha256 = Column(String(64))
    method = Column(String(40))
    retrieved_at = Column(String(60))
    record_type = Column(String(30))
    record_id = Column(Integer)


class Chunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    content = Column(Text)
    embedding = Column(Vector(768))


def initialize():
    with engine.begin() as c:
        c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
