# This Is For The Business Logic, If Feeds From The Repository And Passes to The Controller

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.repository.users_repository import create_user, get_user_by_email
from app.api.schemas.user_schema import UserCreate, UserLogin
from app.api.security.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.api.models.user_model import User
from app.api.services.email_services import EmailService


    
# THIS IS THE EMAIL SERVICE FUNCTION
email_service = EmailService()


# THIS IS THE SIGN UP FUNCTION
async def signup(db: AsyncSession, user: UserCreate) -> str:
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User already exists"
        )
    
    user.password = await hash_password(user.password)
    
    created_user = await create_user(db, user)  # Ensure to await the user creation

    # Send verification email
    await email_service.handle_email_verification(db, user.email, user.first_name)

    return JSONResponse(
        status_code=201,  # HTTP status for "Created"
        content={"message": "User created. Please check your email to verify your account."}
    )
    
    

# THIS IS THE SIGN IN FUNCTION
async def signin(db: AsyncSession, user: UserLogin) -> dict:
    existing_user = await get_user_by_email(db, user.email)
    if not existing_user or not await verify_password(user.password, existing_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )
    
    # Generate JWT token
    token_data = {
        "id": str(existing_user.id),
        "email": existing_user.email,
        "first_name": existing_user.first_name,
        "last_name": existing_user.last_name,
        "is_active": existing_user.is_active,
        "role_id": existing_user.role_id
        # Add more fields as needed
    }
    access_token = await create_access_token(user_data=token_data)  # Generate access token
    refresh_token = await create_refresh_token(user_data=token_data)  # Generate refresh token
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

