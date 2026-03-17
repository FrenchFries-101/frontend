from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Word

router = APIRouter(prefix="/word", tags=["Word"])


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Return all top-level word categories."""
    results = db.query(Word.category).distinct().all()
    return [r[0] for r in results]


@router.get("/subcategories")
def get_subcategories(category: str, db: Session = Depends(get_db)):
    """Return all sub-categories under a given top-level category."""
    results = (
        db.query(Word.subcategory)
        .filter(Word.category == category)
        .distinct()
        .all()
    )
    if not results:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    return [r[0] for r in results]


@router.get("/words")
def get_words(category: str, subcategory: str, db: Session = Depends(get_db)):
    """Return all words (English + definition) under a given category and sub-category."""
    words = (
        db.query(Word)
        .filter(Word.category == category, Word.subcategory == subcategory)
        .all()
    )
    if not words:
        raise HTTPException(status_code=404, detail="No words found for this category")
    return [{"english": w.english, "chinese": w.chinese} for w in words]
