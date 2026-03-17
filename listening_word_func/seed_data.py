"""
Run this script to initialise database tables and insert seed data.
Usage: python seed_data.py
"""
from database import engine, SessionLocal, Base
from models import Word, Section, Answer, UserScore

Base.metadata.create_all(bind=engine)

WORDS = [
    # Academic Subject - Mathematics
    ("Academic Subject", "Mathematics", "derivative", "rate of change of a function"),
    ("Academic Subject", "Mathematics", "matrix", "rectangular array of numbers"),
    ("Academic Subject", "Mathematics", "integral", "area under a curve"),
    ("Academic Subject", "Mathematics", "vector", "quantity with magnitude and direction"),
    ("Academic Subject", "Mathematics", "probability", "likelihood of an event occurring"),
    ("Academic Subject", "Mathematics", "theorem", "proven mathematical statement"),
    ("Academic Subject", "Mathematics", "coefficient", "numerical factor in a term"),
    ("Academic Subject", "Mathematics", "polynomial", "expression with multiple terms"),
    # Academic Subject - Computer Science
    ("Academic Subject", "Computer Science", "algorithm", "step-by-step problem-solving procedure"),
    ("Academic Subject", "Computer Science", "recursion", "function that calls itself"),
    ("Academic Subject", "Computer Science", "database", "organised collection of structured data"),
    ("Academic Subject", "Computer Science", "compiler", "translates source code to machine code"),
    ("Academic Subject", "Computer Science", "encryption", "encoding data to prevent unauthorised access"),
    ("Academic Subject", "Computer Science", "bandwidth", "data transfer capacity of a network"),
    ("Academic Subject", "Computer Science", "latency", "delay in data transmission"),
    ("Academic Subject", "Computer Science", "concurrency", "simultaneous execution of processes"),
    # Academic Subject - Civil Engineering
    ("Academic Subject", "Civil Engineering", "foundation", "base structure supporting a building"),
    ("Academic Subject", "Civil Engineering", "concrete", "construction material made from cement and aggregate"),
    ("Academic Subject", "Civil Engineering", "beam", "horizontal structural member"),
    ("Academic Subject", "Civil Engineering", "reinforcement", "steel bars embedded in concrete"),
    ("Academic Subject", "Civil Engineering", "load-bearing", "capable of supporting weight"),
    ("Academic Subject", "Civil Engineering", "drainage", "system for removing excess water"),
    ("Academic Subject", "Civil Engineering", "excavation", "digging or removing earth"),
    ("Academic Subject", "Civil Engineering", "compressive strength", "resistance to being crushed"),
    # Academic Subject - Mechanical Engineering
    ("Academic Subject", "Mechanical Engineering", "gear", "toothed wheel that transmits motion"),
    ("Academic Subject", "Mechanical Engineering", "torque", "rotational force"),
    ("Academic Subject", "Mechanical Engineering", "friction", "resistance between surfaces in contact"),
    ("Academic Subject", "Mechanical Engineering", "hydraulic", "operated by pressurised fluid"),
    ("Academic Subject", "Mechanical Engineering", "bearing", "component that reduces rotational friction"),
    ("Academic Subject", "Mechanical Engineering", "tensile strength", "resistance to being stretched"),
    ("Academic Subject", "Mechanical Engineering", "thermal conductivity", "ability to conduct heat"),
    ("Academic Subject", "Mechanical Engineering", "vibration", "rapid back-and-forth motion"),
    # Academic English - Group Discussion
    ("Academic English", "Group Discussion", "In my opinion", "used to express a personal view"),
    ("Academic English", "Group Discussion", "I would like to add that", "used to contribute an additional point"),
    ("Academic English", "Group Discussion", "Could you elaborate on that?", "asking someone to explain in more detail"),
    ("Academic English", "Group Discussion", "I see your point, however", "acknowledging a view before disagreeing"),
    ("Academic English", "Group Discussion", "To summarize what has been said", "recapping the discussion so far"),
    ("Academic English", "Group Discussion", "Shall we move on to the next point?", "suggesting the group progresses"),
    # Academic English - Presentation
    ("Academic English", "Presentation", "Today I am going to talk about", "standard opening phrase"),
    ("Academic English", "Presentation", "As you can see from the slide", "directing audience attention to a visual"),
    ("Academic English", "Presentation", "To conclude", "signalling the end of the talk"),
    ("Academic English", "Presentation", "Are there any questions?", "inviting audience questions"),
    ("Academic English", "Presentation", "Moving on to my next point", "transitioning between topics"),
    ("Academic English", "Presentation", "This graph illustrates", "introducing a data visualisation"),
    # Academic English - Academic Writing
    ("Academic English", "Academic Writing", "This paper aims to", "stating the purpose of the paper"),
    ("Academic English", "Academic Writing", "Evidence suggests that", "introducing research-backed claims"),
    ("Academic English", "Academic Writing", "In contrast", "highlighting a difference"),
    ("Academic English", "Academic Writing", "Furthermore", "adding a supporting point"),
    ("Academic English", "Academic Writing", "It can be concluded that", "summarising findings"),
    ("Academic English", "Academic Writing", "According to previous studies", "citing earlier research"),
]

# Listening material: Cambridge IELTS 5-20, 4 tests per book, 4 sections per test (placeholder)
SECTION_NAMES = [
    "Recommendation for local facilities",
    "Pottery workshop introduction",
    "Study group discussion",
    "Lecture on environmental issues",
]

SAMPLE_ANSWERS = ["A", "B", "happy", "museum", "Tuesday", "red", "7", "north", "garden", "false"]


def seed():
    db = SessionLocal()

    # Clear existing data (safe to re-run)
    db.query(Answer).delete()
    db.query(UserScore).delete()
    db.query(Section).delete()
    db.query(Word).delete()

    # Insert words
    for category, subcategory, english, chinese in WORDS:
        db.add(Word(category=category, subcategory=subcategory, english=english, chinese=chinese))

    # Insert listening material (placeholder)
    for cambridge_id in range(5, 21):       # books 5 to 20
        for test_id in range(1, 5):         # Test 1-4
            for section_num in range(1, 5): # Section 1-4
                section = Section(
                    cambridge_id=cambridge_id,
                    test_id=test_id,
                    section_number=section_num,
                    section_name=SECTION_NAMES[section_num - 1],
                    audio_path=f"media/audio/cambridge{cambridge_id}_test{test_id}_section{section_num}.mp3",
                    image_path=f"media/images/cambridge{cambridge_id}_test{test_id}_section{section_num}.png",
                )
                db.add(section)
                db.flush()  # get section.id before inserting answers

                for q_num in range(1, 11):  # 10 questions per section
                    db.add(Answer(
                        section_id=section.id,
                        question_number=q_num,
                        answer_text=SAMPLE_ANSWERS[(q_num - 1) % len(SAMPLE_ANSWERS)],
                    ))

    db.commit()
    db.close()
    print("Seed data inserted successfully.")


if __name__ == "__main__":
    seed()
