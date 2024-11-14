import logging
import time
import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from itsdangerous import Serializer, URLSafeTimedSerializer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select  # For async queries
from jose import JWTError
import jwt
from passlib.context import CryptContext

from app.api.config.settings import settings
from app.api.database.db import get_db
from app.api.models.user_model import User

passwd_context = CryptContext(schemes=["bcrypt"])


def generate_passwd_hash(password: str) -> str:
    return passwd_context.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return passwd_context.verify(password, hash)




async def decode_token(token: str, db: AsyncSession = Depends(get_db)) -> User:
    try:
        # Decode the JWT token
        token_data = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = token_data.get("data", {}).get("email")  # Adjust this line to handle nested structure
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Check for expiration
        if 'exp' in token_data and token_data['exp'] < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
        # Fetch the user from the database using async query
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already activated")
        
        return user  # Return the User instance

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    
    
    
    
    

async def decode_token_skip_active_check(token: str, db: AsyncSession = Depends(get_db)) -> User:
    try:
        # Decode the JWT token
        token_data = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = token_data.get("data", {}).get("email")  # Fix this to "sub"
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Check for expiration
        if 'exp' in token_data and token_data['exp'] < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
        # Fetch the user from the database using async query
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user  # Return the User instance
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")






async def create_url_safe_token(data: dict) -> str:
    return Serializer.dumps(data)




async def decode_url_safe_token(token: str) -> dict:
    try:
        token_data = Serializer.loads(token)
        return token_data
    except Exception as e:
        logging.error(str(e))
        return None
