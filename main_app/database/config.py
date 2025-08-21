from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://progress_user:progress_password@localhost:5432/progress_tracker")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={
        "client_encoding": "utf8",
        "options": "-c timezone=UTC"
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()