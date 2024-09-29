from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class OperatorModel(Base):
    __tablename__ = 'operators'
    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=False)

class QuestionModel(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    question_text = Column(String)
    status = Column(String) 
