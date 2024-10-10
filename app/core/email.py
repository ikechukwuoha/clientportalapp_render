from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config.settings import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAIL_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_SERVER,
    MAIL_FROM_NAME=settings.PROJECT_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
)


async def send_verification_email(email: str, token: str):
    message = MessageSchema(
        subject="Email Verification",
        recipients=[email],
        body=f"Click the link to verify your email: http://localhost:8000/verify-email?token={token}",
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
