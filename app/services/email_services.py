from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config.settings import settings
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import EmailStr

from app.security.security import create_verification_token

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

    async def send_verification_email(self, email: str, token: str, first_name: str):
        # HTML email template with purple activation button on white background
        html = f"""
        <html>
            <body style="background-color: #ffffff; font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; text-align: center; box-shadow: 0 0 10px rgba(0,0,0,0.1); border-radius: 10px; padding: 20px;">
                    <h2 style="color: #4b0082;">Hello {first_name},</h2>
                    <h2 style="color: #4b0082;">Verify Your Email Address</h2>
                    <p>Click the button below to verify your email address and activate your account:</p>
                    <a href="http://localhost:8000/api/verify-email?token={token}" 
                    style="display: inline-block; padding: 15px 25px; font-size: 16px; color: #ffffff; background-color: #6A0DAD; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                        Activate Account
                    </a>
                    <p style="margin-top: 20px;">If the button above doesn't work, copy and paste the following link into your browser:</p>
                    <p><a href="http://localhost:8000/api/verify-email?token={token}" style="color: #6A0DAD;">http://localhost:8000/api/verify-email?token={token}</a></p>
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

    async def handle_email_verification(self, db, email, first_name):
        verification_token = create_verification_token(data={"email": email})
        await self.send_verification_email(email, verification_token, first_name)

        
        
        
class PasswordResetMailService:
    async def send_reset_password_email(self, email: EmailStr, token: str, first_name: str):
        # Use settings.DOMAIN to create the reset link dynamically
        link = f"{settings.DOMAIN}/api/reset-password/{token}"
        # HTML content with purple on white styling, incorporating the first name
        html_content = f"""
        <html>
        <body style="background-color: #ffffff; color: #4B0082; padding: 20px; font-family: Arial, sans-serif; text-align: center;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 2px solid #4B0082; border-radius: 10px;">
                <h2 style="color: #4B0082;">Password Reset Request</h2>
                <p style="font-size: 16px; color: #333;">
                    Hello {first_name}, <br><br>
                    You requested to reset your password. Please click the button below to reset it:
                </p>
                <a href={link}
                   style="background-color: #4B0082; color: #fff; padding: 10px 20px; text-decoration: none; font-size: 16px; border-radius: 5px;">
                    Reset Password
                </a>
                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    If you did not request this password reset, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create the message object with the styled HTML content
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],  
            body=html_content,  # Using the styled HTML content
            subtype="html"  # Specifying that the content is HTML
        )

        # Initialize FastMail and send the email
        fm = FastMail(conf)
        await fm.send_message(message)



