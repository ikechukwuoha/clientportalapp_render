#The Handles The Routing For All User Logic
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from app.controllers.auth_controllers import AuthController
from app.database.db import get_db
from app.schemas.user_schema import UserLogin, UserCreate
from app.models import user_model
from app.services.user_services import signin, signup



router = APIRouter()
auth_controller = AuthController()

# Route for User Signup
@router.post("/auth/signup", tags=["auth"])
async def signup_route(user: UserCreate, db: Session = Depends(get_db)):
    return await auth_controller.register_user(db, user)


# Route for User Signin (Login)
@router.post("/auth/signin", tags=["auth"])
async def signin_route(user: UserLogin, db: Session = Depends(get_db)):
    return await auth_controller.login_user(db, user)