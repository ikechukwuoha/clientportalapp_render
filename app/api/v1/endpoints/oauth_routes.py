import logging
import os
import uuid
from fastapi import APIRouter, Request, HTTPException, Depends
from authlib.integrations.starlette_client import OAuth, OAuthError
from sqlalchemy import func, select
from app.api.database.db import get_db
from app.api.models.user_model import User
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from authlib.jose import jwt
import httpx
import json

from app.api.security.security import create_access_token, create_refresh_token, hash_password

load_dotenv()

router = APIRouter()

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://oauth2.googleapis.com/token',
    # authorize_params=None,
    # refresh_token_url=None,
    client_kwargs={
        'scope': 'email openid profile',
        'redirect_url': 'http://localhost:8000/callback/google'
    },
    server_metadata_url= 'https://accounts.google.com/.well-known/openid-configuration',
)

oauth.register(
    name='apple',
    client_id=os.getenv("APPLE_CLIENT_ID"),
    client_secret=os.getenv("APPLE_CLIENT_SECRET"),
    authorize_url='https://appleid.apple.com/auth/authorize',
    access_token_url='https://appleid.apple.com/auth/token',
    authorize_params=None,
    refresh_token_url=None,
    redirect_uri='http://localhost:8000/api/callback/apple',
    client_kwargs={'scope': 'openid email'},
)


async def get_jwks_uri() -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://accounts.google.com/.well-known/openid-configuration")
        response.raise_for_status()
        return response.json()['jwks_uri']

async def get_jwks(jwks_uri: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()
            logging.debug(f"JWKS Response: {response.json()}")
            return response.json()
    except httpx.RequestError as e:
        logging.error(f"Error while fetching JWKS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while fetching JWKS: {str(e)}")


async def verify_id_token(id_token: str):
    jwks_uri = await get_jwks_uri()  # Fetch JWKS URI
    jwks = await get_jwks(jwks_uri)   # Get JWKS

    # Decode the header to extract 'kid'
    header = jwt.get_unverified_header(id_token)
    kid = header.get("kid")

    # Find the key that matches the 'kid'
    for key in jwks['keys']:
        if key['kid'] == kid:
            try:
                # Decode the token using the public key
                decoded_token = jwt.decode(id_token, key, claims_options={"aud": {"essential": False}})
                return decoded_token
            except Exception as e:
                # Handle token verification errors
                raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/login/google", tags=["auth"])
async def login_google(request: Request):
    redirect_uri = request.url_for('callback_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)



@router.get("/callback/google", tags=["auth"])
async def callback_google(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")
    
    user_info = token.get('userinfo')
    
    if user_info:
        
        try:
            # Check if the user already exists
            result = await db.execute(select(User).filter_by(email=user_info['email']))
            user = result.scalar_one_or_none()

            if user:
                # Update existing user
                user.first_name = user_info['given_name']
                user.last_name = user_info['family_name']
                # user.picture = user_info['picture']
                # user.email_verified = user_info['email_verified']
                user.updated_at = func.now()  # Update the timestamp
            else:
                # Generate a hashed placeholder password
                random_password = uuid.uuid4().hex
                hashed_password = await hash_password(random_password)
                
                # Create a new user with hashed password
                user = User(
                    first_name=user_info['given_name'],
                    last_name=user_info['family_name'],
                    email=user_info['email'],
                    password=hashed_password,  # Use your bcrypt hashed password
                    is_active=True,
                    created_at=func.now(),  # Set the creation timestamp
                    updated_at=func.now()
                )
                db.add(user)
            
            await db.commit()
            
            # Optionally refresh the user object to get updated values (e.g., `id` after commit)
            await db.refresh(user)
            
            
            # Include user info directly in the access token payload
            access_token = await create_access_token(user_data={
                "email": user.email,
                "first_name": user.first_name, 
                "last_name": user.last_name,
                "picture": user_info.get('picture')
            })

            # Generate a refresh token
            refresh_token = await create_refresh_token(user_data={
                "email": user.email
            })

            # Return only the tokens
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
    
        except Exception as e:
            # Log the error for debugging purposes
            logging.error(f"Error creating/updating user: {str(e)}")
            raise HTTPException(status_code=500, detail="Could not create or update user.")
    
    
    

@router.get("/api/login/apple", tags=["auth"])
async def login_apple(request: Request):
    redirect_uri = request.url_for('callback_apple')
    return await oauth.apple.authorize_redirect(request, redirect_uri)





@router.get("/api/callback/apple", tags=["auth"])
async def callback_apple(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.apple.authorize_access_token(request)
        user_info = await oauth.apple.parse_id_token(request, token)
        user = db.query(User).filter(User.email == user_info['email']).first()
        if not user:
            user = User(email=user_info['email'])
            db.add(user)
            db.commit()
        return user_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")
