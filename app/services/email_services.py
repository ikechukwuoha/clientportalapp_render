from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user_model import User
from app.security.security import create_access_token, create_verification_token, verify_password_reset_token, hash_password
from app.config.email_config import EmailService, PasswordResetMailService




# Initialize services
email_service = EmailService()
password_reset_service = PasswordResetMailService()




# Email Verification Logic
async def verify_email_logic(token: str, db: Session, user: User):
    # Check if the email is already verified
    if user.is_active:
        raise HTTPException(status_code=400, detail="This Token Has Been Used or Expired, Please Contact Admin")

    # Update the user's active status
    user.is_active = True
    db.commit()

    # Generate the access token
    token_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": user.is_active
    }
    access_token = create_access_token(data=token_data)  # Generate token here

    # Optionally, send verification email if needed
    # await email_service.handle_email_verification(db, user.email, user.first_name)

    return access_token  # Return the generated access token





# Password Reset Request Logic
async def password_reset_request_logic(email: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    
    token = create_verification_token({"sub": user.email})
    await password_reset_service.send_reset_password_email(user.email, token, user.first_name)
    return user





# Reset Password Logic
async def reset_password_logic(token: str, new_password: str, db: Session):
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.password = hash_password(new_password)
    db.commit()
    return user
