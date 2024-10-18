import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db  # Assuming you have a get_db dependency
from app.models.user_model import User



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




from fastapi import Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.models import User, Role
from app.database import get_db

# Function to verify if the user has the required role
async def verify_role(
    role_id: str, db: Session = Depends(get_db)
) -> None:
    # Query the Role for the user's role_id
    user = db.query(User).filter(User.role_id == role_id).first()

    if not user or not user.role:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Check if the user's role_name is either 'Admin' or 'Super Admin'
    if user.role.name not in ["Admin", "Super Admin"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    # If the role is 'Admin' or 'Super Admin', the function continues
