from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # New email configuration settings
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_TOKEN_EXPIRE_MINUTES: int
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    

    # Other configurations
    route_prefix: str = "/api"

    class Config:
        env_file = ".env"  # Load settings from .env file
        extra = "allow"    # Allow extra fields in the environment file

# Initialize settings
settings = Settings()
