from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config.settings import settings
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import EmailStr



conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAIL_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_SERVER,
    MAIL_FROM_NAME=settings.PROJECT_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

class EmailService:
    def __init__(self):
        self.fm = FastMail(conf)

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def send_verification_email(self, email: str, token: str):
        message = MessageSchema(
            subject="Email Verification",
            recipients=[email],
            body=f"Click the link to verify your email: http://localhost:8000/verify-email?token={token}",
            subtype="html"
        )
        await self.fm.send_message(message)

    async def handle_email_verification(self, db, email):
        verification_token = self.create_access_token(data={"email": email})
        await self.send_verification_email(email, verification_token)

class PasswordResetMailService:
    async def send_reset_password_email(email: EmailStr, token: str):
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],  
            body=f"Click the link to reset your password: http://localhost:4000/reset-password?token={token}",
            subtype="html"
        )
        fm = FastMail(conf)
        await fm.send_message(message)