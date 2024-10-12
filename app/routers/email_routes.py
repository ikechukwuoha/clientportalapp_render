from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError, jwt
from app.config.settings import settings
from app.database.db import get_db
from app.dependencies.token_dependency import decode_token, get_user_by_email_from_token, check_user_is_not_verified
from app.dependencies.user_dependency import get_active_user_by_email, get_user_by_email
from app.models.user_model import User
from app.schemas.user_schema import Email
from app.services.email_services import EmailService, PasswordResetMailService
from app.security.security import create_verification_token, verify_password_reset_token, hash_password, create_access_token
from app.schemas.user_schema import ResetPassword, ResetPasswordRequest


router = APIRouter()
email_service = EmailService()

@router.get("/verify-email", tags=["auth"])
async def verify_email(token: str, db: Session = Depends(get_db), response: Response = None, user: User = Depends(decode_token)):
    # Check if the email is already verified
    if user.is_active:
        raise HTTPException(status_code=400, detail="This Token Has Been Used or Expired, Please Contact Admin")
    
    # Update the user's active status
    user.is_active = True
    db.commit()
    
    # Create access token
    token_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": user.is_active
    }
    access_token = create_access_token(data=token_data)

    # Set the token in the cookie
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite='Strict')

    return {"message": "Email verified successfully"}




@router.post("/password-reset-request", tags=["auth"])
async def password_reset_request(email: Email, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
            )
    
    token = create_verification_token({"sub": user.email})
    
    # Create an instance of PasswordResetMailService
    password_reset_service = PasswordResetMailService()
    
    # Pass user's first name along with email and token
    await password_reset_service.send_reset_password_email(user.email, token, user.first_name)
    
    return {"message": "Password reset link sent to your email."}






# FUNCTION FOR RESETTING YOUR PASSWORD
@router.post("/reset-password/{token}", tags=["auth"])
async def reset_password(token: str, new_password: ResetPassword, db: Session = Depends(get_db)):
    email = verify_password_reset_token(token)
    print(f"Email extracted from token: {email}")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Hash new password and save
    user.password = hash_password(new_password.password)
    db.commit()
    
    return {"message": "Password updated successfully."}