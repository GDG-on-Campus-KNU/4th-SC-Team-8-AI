from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
from db.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# 비밀번호 인코딩
password_encoded = quote_plus(DB_PASSWORD)

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# 엔진과 세션 설정
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
