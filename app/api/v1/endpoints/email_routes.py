from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError, jwt
from app.api.config.settings import settings
from app.api.controllers.email_controller import EmailController
from app.api.database.db import get_db
from app.api.dependencies.dependencies import decode_token, get_user_by_email_from_token, check_user_is_not_verified,  get_active_user_by_email, get_user_by_email
from app.api.models.user_model import User
from app.api.schemas.user_schema import Email
from app.api.services.email_services import EmailService, PasswordResetMailService
from app.api.security.security import create_refresh_token, create_verification_token, verify_password_reset_token, hash_password, create_access_token
from app.api.schemas.user_schema import ResetPassword, ResetPasswordRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.utils import decode_token_skip_active_check


router = APIRouter()



@router.get("/verify-email", tags=["auth"])
async def verify_email(token: str, db: AsyncSession = Depends(get_db), response: Response = None, user: User = Depends(decode_token)):
    # Assuming EmailController.verify_email only handles activation now
    await EmailController.verify_email(db, user)
    # Create the refresh token
    refresh_token = await create_refresh_token({"email": user.email, "first_name": user.first_name})
    
    # Set the tokens as cookies
    response.set_cookie(key="access_token", value=token, httponly=True, samesite='Strict')
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite='Strict')
    
    return {"message": "Email verified successfully"}








# Route to Send Password Reset Link
@router.post("/password-reset-request", tags=["auth"])
async def password_reset_request(email: Email, db: AsyncSession = Depends(get_db)):
    await EmailController.password_reset_request(email.email, db)
    return {"message": "Password reset link sent to your email."}





# Route to Reset Password
@router.post("/reset-password/{token}", tags=["auth"])
async def reset_password(
    token: str, 
    new_password: ResetPassword, 
    db: AsyncSession = Depends(get_db), 
    user: User = Depends(decode_token_skip_active_check)
):
    await EmailController.reset_password(user, new_password, db)
    return {"message": "Password updated successfully."}
