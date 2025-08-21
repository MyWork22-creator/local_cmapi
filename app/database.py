from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import urllib.parse
from .core.config import settings

# SQLAlchemy setup
engine_kwargs = {"echo": True, "pool_pre_ping": True}

if settings.DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///./{settings.DB_NAME}.db"
    # connect_args is needed for SQLite
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif settings.DB_TYPE == "mysql":
    # MySQL connection URL
    DB_PASSWORD_ENCODED = urllib.parse.quote_plus(settings.DB_PASSWORD)
    DATABASE_URL = (
        f"mysql+pymysql://{settings.DB_USER}:{DB_PASSWORD_ENCODED}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
else:
    raise ValueError(f"Unsupported DB_TYPE: {settings.DB_TYPE}")

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
