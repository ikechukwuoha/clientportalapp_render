# This Is For The Business Logic, If Feeds From The Repository And Passes to The Controller


from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.email import send_verification_email
from app.repository.users_repository import create_user, get_user_by_email
from app.schemas.user_schema import UserCreate, UserLogin
from app.security.security import create_access_token, hash_password, verify_password
from app.models.user_model import User



async def signup(db: Session, user: UserCreate) -> str:  # Return only the token
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user.password = hash_password(user.password)
    created_user = create_user(db, user)  # Create the user in the database
    
    # Create the JWT token with user details
    token_data = {
        "id": str(created_user.id),
        "sub": created_user.email,
        "first_name": created_user.first_name,
        "last_name": created_user.last_name,
        "is_active": created_user.is_active,
        # Add more fields as needed
    }
    
    token = create_access_token(data=token_data)  
    
    return token
    

# async def signup(db: Session, user: UserCreate) -> str:
#     existing_user = get_user_by_email(db, user.email)
#     if existing_user:
#         raise HTTPException(status_code=400, detail="User already exists")
    
#     user.password = hash_password(user.password)
#     created_user = create_user(db, user)  # Create the user in the database

#     # Send verification email
#     verification_token = create_access_token(data={"email": user.email})  # Create a verification token
#     await send_verification_email(user.email, verification_token)

#     return "User created. Please check your email to verify your account."



    



async def signin(db: Session, user: UserLogin) -> str:
    existing_user = get_user_by_email(db, user.email)
    if not existing_user or not verify_password(user.password, existing_user.password):
        raise ValueError("Invalid credentials")
    
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
