from datetime import datetime
from fastapi import Depends, HTTPException, status
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session
from app.schemas.user_schema import User as Users
from app.models.user_model import User
from app.database.db import get_db
from app.config.settings import settings
from app.security.security import create_access_token
import logging

# Dependency to decode the token and manage token errors
# def decode_token(token: str):
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         return payload
#     except ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


# Dependency to decode the token and fetch the user

def decode_token(token: str, db: Session = Depends(get_db)) -> User:
    try:
        # Log the token received
        logging.info(f"Token received: {token}")
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        #print("This is the Payload from the Decoded token", payload)
        
        # Ensure the token has not expired
        if payload["exp"] < datetime.now().timestamp():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")

        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token: Email not found")
        
        user = db.query(User).filter(User.email == email).first()
        #print("This is the data fetched from the User", user)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user
    
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


    
    
    

# Dependency to get the user by email and handle user-related errors
def get_user_by_email_from_token(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token)
    email = payload.get("email")

    if email is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user



# Dependency to check if the user is already verified
def check_user_is_not_verified(user: User):
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This account is already verified")
    return user



