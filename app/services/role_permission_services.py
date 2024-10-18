from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_model import User  # Assuming you have a User model
import uuid


class RoleAssignment(BaseModel):
    role_id: uuid.UUID  # A single role ID to be assigned



async def create_role(db: Session, role_name: str):
    role = Role(name=role_name)
    try:
        db.add(role)
        db.commit()
        db.refresh(role)
    except Exception as e:
        # Handle or log the exception as needed
        db.rollback() 
        raise e  # Reraise the exception after rollback
    return role




async def delete_role(db: Session, role_id: uuid.UUID):
    role = db.query(Role).filter(Role.id == role_id).first()
    if role:
        db.delete(role)
        db.commit()
        return True
    return False



async def add_role_to_user(db: Session, user_id: uuid.UUID, role_id: uuid.UUID):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    if user and role:
        user.role = role  # Assuming 'role' is the correct attribute for the relationship
        db.commit()
        return True
    return False






async def remove_role_from_user(db: Session, user_id: uuid.UUID):
    user = db.query(User).filter(User.id == user_id).first()
    
    if user and user.role_id:  # Ensure the user has a role assigned
        user.role_id = None  # Remove the role by setting role_id to None
        db.commit()
        return True
    
    return False




async def create_permission(db: Session, permission_name: str):
    permission = Permission(name=permission_name)
    try:
        db.add(permission)
        db.commit()
        db.refresh(permission)
    except Exception as e:
        # Handle or log the exception as needed
        db.rollback()  # Roll back the session in case of an error
        raise e  # Reraise the exception after rollback
    return permission



async def delete_permission(db: Session, permission_id: uuid.UUID):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if permission:
        db.delete(permission)
        db.commit()
        return True
    return False





# A Function That Adds Permissions or a Single Permission to a role
async def add_permissions_to_role(db: Session, role_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> int:
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return 0  # Return 0 if role is not found

    added_count = 0

    # Add each permission to the role
    for permission_id in permission_ids:
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if permission and permission not in role.permissions:
            role.permissions.append(permission)
            added_count += 1  # Increment count for each permission added

    db.commit()  # Commit after all permissions are added
    return added_count  # Return the count of added permissions






async def remove_permissions_from_role(db: Session, role_id: uuid.UUID, permission_ids: list):
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if role:
        for permission_id in permission_ids:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if permission in role.permissions:
                role.permissions.remove(permission)
        db.commit()
        return True
    return False





# A Function That Adds Permissions or a Single Permission to a role
async def add_permissions_to_user(db: Session, user_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> int:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return 0  # Return 0 if user is not found

    added_count = 0

    # Add each permission to the role
    for permission_id in permission_ids:
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if permission and permission not in user.permissions:
            user.permissions.append(permission)
            added_count += 1  # Increment count for each permission added

    db.commit()  # Commit after all permissions are added
    return added_count  # Return the count of added permissions




# A Function That Revokes Permission From A User
async def remove_permissions_from_user(db: Session, user_id: uuid.UUID, permission_ids: list):
    user = db.query(User).filter(User.id == user_id).first()
    
    if user:
        for permission_id in permission_ids:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            if permission in user.permissions:
                user.permissions.remove(permission)
        db.commit()
        return True
    return False