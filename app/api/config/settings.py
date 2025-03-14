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
    REFRESH_TOKEN_EXPIRE_DAYS: int
    DOMAIN: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    SESSION_SECRET_KEY: str
    PAYSTACK_SECRET_KEY:str
    FRAPPE_BASE_URL:str

    
    
    # New email configuration settings
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_TOKEN_EXPIRE_MINUTES: int
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    

    # Other configurations
    ROUTE_PREFIX: str = "/api"

    class Config:
        env_file = ".env"
        extra = "allow"

# Initialize settings
settings = Settings()

