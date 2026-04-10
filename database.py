# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI

DATABASE_URL = "mysql+pymysql://cardData:zxN8TNNP4Ghf4Ksb@124.223.33.28:3306/carddata"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================
# 临时在这里创建 FastAPI 应用
# ======================
app = FastAPI(title="论坛测试接口")

# 直接导入 forum 路由并挂载
from forum import router as forum_router
app.include_router(forum_router)