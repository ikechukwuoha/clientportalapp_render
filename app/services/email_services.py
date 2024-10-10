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



class EmailService:
    def __init__(self):
        self.fm = FastMail(conf)

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now() + timedelta(minutes=settings.EMAIL_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def send_verification_email(self, email: str, token: str):
        # HTML email template with purple activation button on white background
        html = f"""
       <html>
            <body style="background-color: #ffffff; font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; text-align: center; box-shadow: 0 0 10px rgba(0,0,0,0.1); border-radius: 10px; padding: 20px;">
                    <h2 style="color: #4b0082;">Verify Your Email Address</h2>
                    <p>Click the button below to verify your email address and activate your account:</p>
                    <a href="http://localhost:8000/api/verify-email?token={token}" 
                    style="display: inline-block; padding: 15px 25px; font-size: 16px; color: #ffffff; background-color: #6A0DAD; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                        Activate Account
                    </a>
                    <p style="margin-top: 20px;">If the button above doesn't work, copy and paste the following link into your browser:</p>
                    <p><a href="http://localhost:8000/api/verify-email?token={token}" style="color: #6A0DAD;">http://localhost:8000/verify-email?token={token}</a></p>
                </div>
            </body>
        </html>
        """

        message = MessageSchema(
            subject="Email Verification",
            recipients=[email],
            body=html,
            subtype="html"  # Set subtype to HTML
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