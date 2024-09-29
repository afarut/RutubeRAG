from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from os import getenv
DATABASE_URL = getenv("DATABASE_URL", "postgresql://user:password@db:5432/dbname")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Функция для инициализации базы данных."""
    Base.metadata.create_all(bind=engine)

def get_session():
        return SessionLocal()