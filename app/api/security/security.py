import os
from datetime import datetime, timedelta
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from app.api.config.settings import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")





# Load environment variables from .env file
load_dotenv()


# Create a CryptContext to use Bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Cast it to an integer
EMAIL_TOKEN_EXPIRE_MINUTES = int(os.getenv("EMAIL_TOKEN_EXPIRE_MINUTES", 5))





async def hash_password(password: str) -> str:
    """Hashes a password using Bcrypt."""
    return pwd_context.hash(password)



async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)



async def create_access_token(
    user_data: dict, expiry: timedelta = None, refresh: bool = False
) -> str:
    payload = {
        "user": user_data,
        "exp": datetime.now() + (expiry if expiry is not None else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }
    # Correct the call to jwt.encode
    token = jwt.encode(
        payload,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return token


async def create_refresh_token(user_data: dict) -> str:
    payload = {
        "user": user_data,
        "exp": datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),  # Use a longer expiry for refresh tokens
        "jti": str(uuid.uuid4()),  # Generate a unique ID for the refresh token
        "refresh": True,
    }

    token = jwt.encode(
        payload,
        key=settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )

    return token





# Function to create the verification token
async def create_verification_token(data: dict, expiry: timedelta = None) -> str:
    payload = {
        "data": data,
        "exp": datetime.now() + (expiry if expiry is not None else timedelta(minutes=settings.EMAIL_TOKEN_EXPIRE_MINUTES)),
        "jti": str(uuid.uuid4())
    }
    # Correct the call to jwt.encode
    token = jwt.encode(
        payload,  # Pass the payload as the first argument
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return token





async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    try:
        # Decode the token and extract the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        return uuid.UUID(user_id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")






def verify_password_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise JWTError
        return email
    except JWTError:
        raise JWTError("Invalid token")