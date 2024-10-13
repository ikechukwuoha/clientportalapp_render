from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError, jwt
from app.config.settings import settings
from app.controllers.email_controller import EmailController
from app.database.db import get_db
from app.dependencies.token_dependency import decode_token, get_user_by_email_from_token, check_user_is_not_verified
from app.dependencies.user_dependency import get_active_user_by_email, get_user_by_email
from app.models.user_model import User
from app.schemas.user_schema import Email
from app.services.email_services import EmailService, PasswordResetMailService
from app.security.security import create_verification_token, verify_password_reset_token, hash_password, create_access_token
from app.schemas.user_schema import ResetPassword, ResetPasswordRequest


router = APIRouter()


#Route For Email Verification
@router.get("/verify-email", tags=["auth"])
async def verify_email(token: str, db: Session = Depends(get_db), response: Response = None, user: User = Depends(decode_token)):
    access_token = await EmailController.verify_email(token, db, user)  # Capture the access token

    # Set the token in the cookie
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite='Strict')

    return {"message": "Email verified successfully"}





# Route to Send Password Reset Link
@router.post("/password-reset-request", tags=["auth"])
async def password_reset_request(email: Email, db: Session = Depends(get_db)):
    await EmailController.password_reset_request(email.email, db)
    return {"message": "Password reset link sent to your email."}





# Route to Reset Password
@router.post("/reset-password/{token}", tags=["auth"])
async def reset_password(token: str, new_password: ResetPassword, db: Session = Depends(get_db)):
    await EmailController.reset_password(token, new_password, db)
    return {"message": "Password updated successfully."}