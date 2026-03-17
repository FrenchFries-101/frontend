from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from database import get_db
from models import Section, Answer, UserScore

router = APIRouter(prefix="/listening", tags=["Listening"])


# ---------- Request body model ----------

class SubmitScoreRequest(BaseModel):
    cambridge_id: int
    test_id: int
    section_id: int
    score: int
    user_id: int


# ---------- Endpoints ----------

@router.get("/cambridge")
def get_cambridge_list(db: Session = Depends(get_db)):
    """Return all available Cambridge IELTS book numbers."""
    results = db.query(Section.cambridge_id).distinct().order_by(Section.cambridge_id).all()
    return [r[0] for r in results]


@router.get("/tests")
def get_tests(cambridge_id: int, user_id: int, db: Session = Depends(get_db)):
    """
    Return all tests for a given Cambridge IELTS book,
    including how many sections the user has completed in each test.
    """
    test_ids = (
        db.query(Section.test_id)
        .filter(Section.cambridge_id == cambridge_id)
        .distinct()
        .order_by(Section.test_id)
        .all()
    )
    if not test_ids:
        raise HTTPException(status_code=404, detail=f"Cambridge IELTS {cambridge_id} not found")

    result = []
    for (test_id,) in test_ids:
        # total sections in this test
        total_sections = (
            db.query(func.count(Section.id))
            .filter(Section.cambridge_id == cambridge_id, Section.test_id == test_id)
            .scalar()
        )
        # sections this user has already submitted a score for
        completed_sections = (
            db.query(func.count(UserScore.id))
            .join(Section, UserScore.section_id == Section.id)
            .filter(
                Section.cambridge_id == cambridge_id,
                Section.test_id == test_id,
                UserScore.user_id == user_id,
            )
            .scalar()
        )
        result.append({
            "test_id": test_id,
            "total_sections": total_sections,
            "completed_sections": completed_sections,
        })
    return result


@router.get("/sections")
def get_sections(cambridge_id: int, test_id: int, db: Session = Depends(get_db)):
    """Return all sections (number + topic name) for a given test."""
    sections = (
        db.query(Section)
        .filter(Section.cambridge_id == cambridge_id, Section.test_id == test_id)
        .order_by(Section.section_number)
        .all()
    )
    if not sections:
        raise HTTPException(status_code=404, detail="No sections found")
    return [
        {"section_number": s.section_number, "section_name": s.section_name}
        for s in sections
    ]


@router.get("/material")
def get_listening_material(cambridge_id: int, test_id: int, section_id: int, db: Session = Depends(get_db)):
    """
    Return the practice material for a section: audio path, question image path, and answers.
    section_id here refers to section_number (1–4).
    """
    section = (
        db.query(Section)
        .filter(
            Section.cambridge_id == cambridge_id,
            Section.test_id == test_id,
            Section.section_number == section_id,
        )
        .first()
    )
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    answers = (
        db.query(Answer)
        .filter(Answer.section_id == section.id)
        .order_by(Answer.question_number)
        .all()
    )
    return {
        "audio": section.audio_path,
        "image": section.image_path,
        "answers": {str(a.question_number): a.answer_text for a in answers},
    }


@router.post("/submit")
def submit_score(body: SubmitScoreRequest, db: Session = Depends(get_db)):
    """Submit the number of correct answers for a section."""
    section = (
        db.query(Section)
        .filter(
            Section.cambridge_id == body.cambridge_id,
            Section.test_id == body.test_id,
            Section.section_number == body.section_id,
        )
        .first()
    )
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    record = UserScore(
        user_id=body.user_id,
        section_id=section.id,
        score=body.score,
    )
    db.add(record)
    db.commit()
    return {"status": "success", "message": "Score submitted successfully"}
