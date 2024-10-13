# This Is For The Business Logic, If Feeds From The Repository And Passes to The Controller

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.repository.users_repository import create_user, get_user_by_email
from app.schemas.user_schema import UserCreate, UserLogin
from app.security.security import create_access_token, hash_password, verify_password
from app.models.user_model import User
from app.services.email_services import EmailService


    
# THIS IS THE EMAIL SERVICE FUNCTION
email_service = EmailService()


# THIS IS THE SIGN UP FUNCTION
async def signup(db: Session, user: UserCreate) -> str:
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User already exists"
        )
    user.password = hash_password(user.password)
    created_user = create_user(db, user)  # Create the user in the database

    # Send verification email
    await email_service.handle_email_verification(db, user.email, user.first_name)

    return JSONResponse(
        status_code=201,  # HTTP status for "Created"
        content={"message": "User created. Please check your email to verify your account."}
    )


# THIS IS THE SIGN IN FUNCTION

async def signin(db: Session, user: UserLogin) -> str:
    existing_user = get_user_by_email(db, user.email)
    if not existing_user or not verify_password(user.password, existing_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )
    
    # Generate JWT token
    token_data = {
        "id": str(existing_user.id),
        "sub": existing_user.email,
        "first_name": existing_user.first_name,
        "last_name": existing_user.last_name,
        "is_active": existing_user.is_active,
        # Add more fields as needed
    }
    token = create_access_token(data=token_data)
    
    return token
