import os
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
EMAIL_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Cast it to an integer


def create_verification_token(email: str) -> str:
    token_data = {"sub": email}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return token
