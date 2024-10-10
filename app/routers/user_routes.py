#The Handles The Routing For All User Logic
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas.user_schema import UserLogin, UserCreate
from app.models import user_model
from app.services.user_services import signin, signup



router = APIRouter()

@router.post("/auth/signup", tags=["auth"])
async def signup_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return await signup(db, user)




@router.post("/auth/signin", tags=["auth"])
async def signin_endpoint(user: UserLogin, db: Session = Depends(get_db)):
    token = await signin(db, user)
    return {"access_token": token, "token_type": "bearer"}