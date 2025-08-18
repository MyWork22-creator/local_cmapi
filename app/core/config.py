import secrets
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = Field("dev-secret-key-change-me", env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")

    # RSA Keys for RS256 algorithm (optional)
    RSA_PRIVATE_KEY: Optional[str] = Field(None, env="RSA_PRIVATE_KEY")
    RSA_PUBLIC_KEY: Optional[str] = Field(None, env="RSA_PUBLIC_KEY")
    RSA_PRIVATE_KEY_PATH: Optional[str] = Field(None, env="RSA_PRIVATE_KEY_PATH")
    RSA_PUBLIC_KEY_PATH: Optional[str] = Field(None, env="RSA_PUBLIC_KEY_PATH")

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key."""
        return v

    @field_validator('ALGORITHM')
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        """Validate JWT algorithm."""
        supported_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        if v not in supported_algorithms:
            raise ValueError(f"Unsupported JWT algorithm: {v}. Supported: {supported_algorithms}")
        return v

    @classmethod
    def generate_secret_key(cls) -> str:
        """Generate a cryptographically secure secret key."""
        return secrets.token_urlsafe(32)

    def get_signing_key(self) -> str:
        """Get the appropriate signing key based on algorithm."""
        if self.ALGORITHM.startswith('RS'):
            # RSA algorithm - use private key
            if self.RSA_PRIVATE_KEY:
                return self.RSA_PRIVATE_KEY
            elif self.RSA_PRIVATE_KEY_PATH:
                try:
                    with open(self.RSA_PRIVATE_KEY_PATH, 'r') as f:
                        return f.read()
                except FileNotFoundError:
                    raise ValueError(f"RSA private key file not found: {self.RSA_PRIVATE_KEY_PATH}")
            else:
                raise ValueError("RSA algorithm requires RSA_PRIVATE_KEY or RSA_PRIVATE_KEY_PATH")
        else:
            # HMAC algorithm - use secret key
            return self.SECRET_KEY

    def get_verification_key(self) -> str:
        """Get the appropriate verification key based on algorithm."""
        if self.ALGORITHM.startswith('RS'):
            # RSA algorithm - use public key
            if self.RSA_PUBLIC_KEY:
                return self.RSA_PUBLIC_KEY
            elif self.RSA_PUBLIC_KEY_PATH:
                try:
                    with open(self.RSA_PUBLIC_KEY_PATH, 'r') as f:
                        return f.read()
                except FileNotFoundError:
                    raise ValueError(f"RSA public key file not found: {self.RSA_PUBLIC_KEY_PATH}")
            else:
                raise ValueError("RSA algorithm requires RSA_PUBLIC_KEY or RSA_PUBLIC_KEY_PATH")
        else:
            # HMAC algorithm - use secret key
            return self.SECRET_KEY

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(10, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 7, env="REFRESH_TOKEN_EXPIRE_MINUTES")  # 7 days
    JWT_ISSUER: str = Field("fastapi-auth-demo", env="JWT_ISSUER")
    JWT_AUDIENCE: Optional[str] = Field(None, env="JWT_AUDIENCE")

    # Cookie Security
    COOKIE_SECURE: bool = Field(False, env="COOKIE_SECURE")  # Set to True in production with HTTPS
    COOKIE_SAMESITE: str = Field("none", env="COOKIE_SAMESITE")  # "strict", "lax", or "none"
    COOKIE_HTTPONLY: bool = Field(True, env="COOKIE_HTTPONLY")

    # CORS Configuration
    ALLOW_ORIGINS: List[str] = Field(["http://localhost:3000", "http://localhost:8080","http://localhost:5173"], env="ALLOW_ORIGINS")
    ALLOW_CREDENTIALS: bool = Field(True, env="ALLOW_CREDENTIALS")
    ALLOW_METHODS: List[str] = Field(["GET", "POST", "PUT", "DELETE", "OPTIONS"], env="ALLOW_METHODS")
    ALLOW_HEADERS: List[str] = Field(["*"], env="ALLOW_HEADERS")

    # Content Security Policy
    CSP_ENABLED: bool = Field(True, env="CSP_ENABLED")
    CSP_REPORT_ONLY: bool = Field(False, env="CSP_REPORT_ONLY")  # Set to True to only report violations

    # App
    CREATE_ALL_ON_STARTUP: bool = Field(True, env="CREATE_ALL_ON_STARTUP")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")  # development, staging, production

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"

    # pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",  # allow unrelated env vars (e.g., DB_* used elsewhere)
    )


settings = Settings()

