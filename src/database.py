from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import DeclarativeBase

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("SQLALCHEMY_DATABASE_URL not found in environment variables")

# Create SQLAlchemy engine with MariaDB-specific settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,  # Maximum number of database connections in the pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=True  # Set to False in production - this logs all SQL queries
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class using new style
class Base(DeclarativeBase):
    pass

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database (create all tables)
def init_db():
    from models.models import Base  # Adjust this import path based on your project structure
    Base.metadata.create_all(bind=engine)

# You can call this when starting your application
if __name__ == "__main__":
    init_db()