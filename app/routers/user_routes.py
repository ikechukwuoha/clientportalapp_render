#The Handles The Routing For All User Logic
import uuid
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from app.controllers.auth_controllers import AuthController
from app.database.db import get_db
from app.dependencies.dependencies import get_role_name
from app.schemas.user_schema import UserLogin, UserCreate, UserResponse
from app.models import user_model
from app.services.user_services import signin, signup
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession



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





@router.get("/all-users", response_model=List[UserResponse], tags=["users-related-routes"])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    users = db.query(user_model.User).all()

    # Use model_validate to create Pydantic models and convert to dictionaries using model_dump
    return [UserResponse.model_validate(user).model_dump() for user in users]





# Example route using the get_role_name dependency
@router.get("/user-role/{user_id}",  tags=["users-related-routes"])
async def get_user_role(user_id: uuid.UUID, role_name: str = Depends(get_role_name)):
    return {"user_id": user_id, "role_name": role_name}

