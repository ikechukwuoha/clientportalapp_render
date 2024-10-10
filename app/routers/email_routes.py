from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.database.db import get_db
from app.models.user_model import User
from app.services.email_services import EmailService, PasswordResetMailService
from app.security.mail_token import create_password_reset_token, verify_password_reset_token
from app.security.security import hash_password
from app.schemas.user_schema import Email, ResetPassword

router = APIRouter()
email_service = EmailService()




@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    print("Endpoint hit")
    try:
        payload = jwt.decode(token, email_service.SECRET_KEY, algorithms=[email_service.ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        user.is_active = True
        db.commit()
        return {"message": "Email verified successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

@router.post("/reset-password", status_code=status.HTTP_200_OK)
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

@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(email: Email, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.email).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    
    token = create_password_reset_token({"sub": user.email})
    await PasswordResetMailService.send_reset_password_email(user.email, token)
    
    return {"message": "Password reset link sent to your email."}