from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Update username, password, and database name here
DATABASE_URL = "mysql+pymysql://root:Cqrs7jkgiz-p@localhost:3306/agile_app"  

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
