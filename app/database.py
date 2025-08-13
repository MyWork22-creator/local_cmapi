import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import urllib.parse

# Load environment variables from .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = urllib.parse.quote(os.getenv("DB_PASSWORD"))
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_TYPE = os.getenv("DB_TYPE", "mysql")  # Default to mysql, can be 'sqlite'

# Database URL configuration
if DB_TYPE.lower() == "sqlite":
    DATABASE_URL = f"sqlite:///./{DB_NAME or 'todo.db'}"
    engine_kwargs = {"echo": True}
else:
    # MySQL connection URL
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine_kwargs = {"echo": True, "pool_pre_ping": True}
print("Database URL : ",DATABASE_URL)
# SQLAlchemy setup
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
