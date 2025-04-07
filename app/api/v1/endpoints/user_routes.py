# #The Handles The Routing For All User Logic
# import uuid
# from fastapi import APIRouter, Depends, status, HTTPException, Response
# from sqlalchemy.orm import Session
# from app.api.controllers.auth_controllers import AuthController
# from app.api.database.db import get_db
# from app.api.dependencies.dependencies import get_role_name
# from app.api.schemas.user_schema import UserLogin, UserCreate, UserResponse
# from app.api.models import user_model
# from app.api.services.user_services import signin, signup
# from typing import List
# from sqlalchemy.ext.asyncio import AsyncSession



# router = APIRouter()
# auth_controller = AuthController()

# # Route for User Signup
# @router.post("/auth/signup", tags=["auth"])
# async def signup_route(user: UserCreate, db: AsyncSession = Depends(get_db)):
#     return await auth_controller.register_user(db, user)



# # Route for User Signin (Login)
# @router.post("/auth/signin", tags=["auth"])
# async def signin_route(user: UserLogin, db: AsyncSession = Depends(get_db)):
#     return await auth_controller.login_user(db, user)



# @router.post("/auth/logout", status_code=status.HTTP_200_OK)
# async def logout(response: Response):
#     """
#     Logs out the user by clearing cookies.
#     """
#     response.delete_cookie(key="access_token", httponly=True)
#     response.delete_cookie(key="refresh_token", httponly=True)
#     return {"message": "Logout successful"}



# @router.get("/all-users", response_model=List[UserResponse], tags=["users-related-routes"])
# async def get_all_users(db: AsyncSession = Depends(get_db)):
#     users = db.query(user_model.User).all()

#     # Use model_validate to create Pydantic models and convert to dictionaries using model_dump
#     return [UserResponse.model_validate(user).model_dump() for user in users]





# # Example route using the get_role_name dependency
# @router.get("/user-role/{user_id}",  tags=["users-related-routes"])
# async def get_user_role(user_id: uuid.UUID, role_name: str = Depends(get_role_name)):
#     return {"user_id": user_id, "role_name": role_name}








#The Handles The Routing For All User Logic
import uuid
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from app.api.controllers.auth_controllers import AuthController
from app.api.database.db import get_db
from app.api.dependencies.dependencies import get_role_name
from app.api.schemas.user_schema import UserLogin, UserCreate, UserResponse
from app.api.models import user_model
from app.api.services.user_services import signin, signup
from app.api.services.settings_service import update_user
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.user_schema import UserUpdate, ChangePassword  # Import the Pydantic schema
from fastapi import UploadFile, File
from app.api.models.user_model import User
from sqlalchemy.future import select
import shutil
import os



router = APIRouter()
auth_controller = AuthController()

# Route for User Signup
@router.post("/auth/signup", tags=["auth"])
async def signup_route(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_controller.register_user(db, user)



# Route for User Signin (Login)
@router.post("/auth/signin", tags=["auth"])
async def signin_route(user: UserLogin, db: AsyncSession = Depends(get_db)):
    return await auth_controller.login_user(db, user)



@router.post("/auth/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """
    Logs out the user by clearing cookies.
    """
    response.delete_cookie(key="access_token", httponly=True)
    response.delete_cookie(key="refresh_token", httponly=True)
    return {"message": "Logout successful"}

@router.get("/get-user/{user_id}", response_model=UserResponse, tags=["users-related-routes"])
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))  # Execute query
    user = result.scalars().first()  # Extract the user object

    if not user:
        raise HTTPException(status_code=404, detail="User not found")  # Handle user not found case

    return UserResponse.model_validate(user)  # Convert ORM model to Pydantic schema


@router.get("/all-users", response_model=List[UserResponse], tags=["users-related-routes"])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))  # Execute async query
    users = result.scalars().all()  # Extract the list of users

    return [UserResponse.model_validate(user) for user in users]


# Example route using the get_role_name dependency
@router.get("/user-role/{user_id}",  tags=["users-related-routes"])
async def get_user_role(user_id: uuid.UUID, role_name: str = Depends(get_role_name)):
    return {"user_id": user_id, "role_name": role_name}


@router.put("/update-user/{user_id}", response_model=UserUpdate, tags=["users-related-routes"])
async def settings_update_user(
    user_id: uuid.UUID, 
    user_update: UserUpdate, 
    db: AsyncSession = Depends(get_db)
):
    # First, get the current user from the database
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert the update data to dictionary using model_dump()
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Remove the email from the update data if it exists
    if 'email' in update_data:
        del update_data['email']
    
    # Now update only the allowed fields
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.put("/change-password/{user_id}", status_code=status.HTTP_200_OK, tags=["users-related-routes"])
async def update_password(
    user_id: uuid.UUID,
    password_data: ChangePassword,
    db: AsyncSession = Depends(get_db)
):
     # Fetch user from database
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify old password
    if not ChangePassword.verify_password(password_data.old_password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Validate new password and confirmation
    try:
        ChangePassword.validate_new_password(password_data.new_password, password_data.confirm_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Hash new password and update user record
    user.password = ChangePassword.hash_password(password_data.new_password)
    await db.commit()
    await db.refresh(user)

    return {"message": "Password changed successfully"}
    
UPLOAD_DIR = "uploads/profile_pictures"

@router.post("/users/{user_id}/upload-profile-picture", tags=["users-related-routes"])
async def upload_profile_picture(user_id: uuid.UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))  
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure the upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save the file
    file_location = f"{UPLOAD_DIR}/{user_id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update user's profile picture URL
    user.profile_picture = file_location
    await db.commit()
    await db.refresh(user)

    return {"message": "Profile picture uploaded successfully", "profile_picture_url": file_location}