import uuid
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.api.database.db import get_db 
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models.role import Role
from app.api.models.user_model import User
from fastapi import Depends, HTTPException, status
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.schemas.user_schema import Email
from app.api.services import user_services
from app.api.utils.errors import AccessTokenRequired, AccountNotVerified, InsufficientPermission, InvalidToken, RefreshTokenRequired
from app.api.utils.utils import decode_token





# Dependency to get role name by user_id
async def get_role_name(user_id: uuid.UUID, db: Session = Depends(get_db)) -> str:
    # Fetch the user from the database by user_id
    user = db.query(User).filter(User.id == user_id).first()

    # Handle case where user is not found
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure that the user has a role assigned
    if not user.role:
        raise HTTPException(status_code=400, detail="A Role has not been Assigned to This user....")

    # Return the role name
    return user.role.name


# Dependency to check if role already exists by name
async def get_role_by_name(role_name: str, db: Session = Depends(get_db)) -> None:
    # Query the Role table to check if the role already exists by name
    role = db.query(Role).filter(Role.name == role_name).first()

    # Raise an exception if the role already exists
    if role:
        raise HTTPException(status_code=400, detail=f"Role '{role_name}' already exists")
    
    # No need to return anything if the role doesn't exist; just proceed
    return None






# Function to check if user is an admin or super admin
async def verify_role_for_admin_or_super_admin(role: str):
    if role not in ["admin", "super admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: only admins or super admins can perform this action"
        )




# Dependency to decode the token and fetch the user
class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)

        token = creds.credentials

        token_data = decode_token(token)

        if not self.token_valid(token):
            raise InvalidToken()

        # if await token_in_blocklist(token_data["jti"]):
        #     raise InvalidToken()

        self.verify_token_data(token_data)

        return token_data

    def token_valid(self, token: str) -> bool:
        token_data = decode_token(token)

        return token_data is not None

    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")

    
class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise AccessTokenRequired()
        


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise RefreshTokenRequired()
        
        


async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_db),
):
    user_email = token_details["user"]["email"]

    user = await user_services.get_user_by_email(user_email, session)

    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> Any:
        if not current_user.is_verified:
            raise AccountNotVerified()
        if current_user.role in self.allowed_roles:
            return True

        raise InsufficientPermission()
    

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



# Function to check if user exists
def get_user_by_email(email: Email, db: Session = Depends(get_db))  -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
    
    return user


# Function to check if user is active
def get_active_user(user: User) -> User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user. Cannot request password reset."
        )
    
    return user



# Combined dependency to check both existence and active status
def get_active_user_by_email(email: Email, db: Session = Depends(get_db)) -> User:
    user = get_user_by_email(email, db)
    get_active_user(user)  # Check if user is active
    return user




#def get_current_user(token_details: dict = Depends())