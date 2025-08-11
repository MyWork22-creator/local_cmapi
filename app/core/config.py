from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = Field("dev-secret-key-change-me", env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 7, env="REFRESH_TOKEN_EXPIRE_MINUTES")  # 7 days
    JWT_ISSUER: str = Field("fastapi-auth-demo", env="JWT_ISSUER")
    JWT_AUDIENCE: Optional[str] = Field(None, env="JWT_AUDIENCE")

    # App
    ALLOW_ORIGINS: List[str] = Field(["*"], env="ALLOW_ORIGINS")
    CREATE_ALL_ON_STARTUP: bool = Field(True, env="CREATE_ALL_ON_STARTUP")

    # pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",  # allow unrelated env vars (e.g., DB_* used elsewhere)
    )


settings = Settings()

