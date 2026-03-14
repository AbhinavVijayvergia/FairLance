from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database stored in the API folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./fairlance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a SQLAlchemy session
    and makes sure it is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

