from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)       # Top-level category: Academic Subject / Academic English
    subcategory = Column(String(50), nullable=False)    # Sub-category: Mathematics / Computer Science, etc.
    english = Column(String(100), nullable=False)
    chinese = Column(String(200), nullable=False)


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cambridge_id = Column(Integer, nullable=False)      # Cambridge IELTS book number, e.g. 5, 6, ..., 20
    test_id = Column(Integer, nullable=False)           # Test number, e.g. 1, 2, 3, 4
    section_number = Column(Integer, nullable=False)    # Section number, e.g. 1, 2, 3, 4
    section_name = Column(String(200), nullable=False)  # Section topic name
    audio_path = Column(String(300), nullable=False)    # Audio file path (placeholder)
    image_path = Column(String(300), nullable=False)    # Question image path (placeholder)

    answers = relationship("Answer", back_populates="section")
    scores = relationship("UserScore", back_populates="section")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    answer_text = Column(String(100), nullable=False)

    section = relationship("Section", back_populates="answers")


class UserScore(Base):
    __tablename__ = "user_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    score = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="scores")
