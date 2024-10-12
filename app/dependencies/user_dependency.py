from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user_schema import Email
from app.database.db import get_db
from app.models.user_model import User





# Function to check if user exists
def get_user_by_email(email: Email, db: Session = Depends(get_db))  -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
    
    return user


# Function to check if user is active
def get_active_user(user: User) -> User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user. Cannot request password reset."
        )
    
    return user



# Combined dependency to check both existence and active status
def get_active_user_by_email(email: Email, db: Session = Depends(get_db)) -> User:
    user = get_user_by_email(email, db)
    get_active_user(user)  # Check if user is active
    return user
