from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.models.user_model import User
from app.api.security.security import create_access_token, create_verification_token, get_current_user_id, verify_password_reset_token, hash_password
from app.api.config.email_config import EmailService, PasswordResetMailService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging





# Initialize services
email_service = EmailService()
password_reset_service = PasswordResetMailService()




async def verify_email_logic(token: str, db: AsyncSession, user: User = Depends(get_current_user_id)):
    if user.is_active:
        raise HTTPException(status_code=400, detail="This Token Has Been Used or Expired, Please Contact Admin")

    # Update the user's active status
    user.is_active = True
    try:
        await db.commit()
        logging.info(f"User {user.email} has been activated successfully.")
        await db.refresh(user)
    except Exception as e:
        logging.error(f"Failed to commit changes for user {user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify email")

    # Generate the access token
    token_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": user.is_active
    }
    access_token = await create_access_token(data=token_data)
    return access_token








# Password Reset Request Logic
async def password_reset_request_logic(email: dict, db: AsyncSession):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first() 
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    
    token_data = {
        "email": user.email,
        "first_name": user.first_name
    }
    
    # Generate the token only once here
    token = await create_verification_token(token_data)  
    await password_reset_service.send_reset_password_email(user.email, token, user.first_name)
    return user





# Reset Password Logic
async def reset_password_logic(email: str, new_password: str, db: AsyncSession):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()  # Get the first user from the result
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password = await hash_password(new_password)  # Hash the password
    await db.commit()  # Commit the changes to the database
    
    return user

