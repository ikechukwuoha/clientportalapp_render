from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.models.role import Role
from app.api.models.permission import Permission
from app.api.models.user_model import User  # Assuming you have a User model
import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.orm import joinedload
class RoleAssignment(BaseModel):
    role_id: uuid.UUID  # A single role ID to be assigned



async def create_role(db: AsyncSession, role_name: str) -> Role:
    result = await db.execute(
        select(Role).filter(Role.name == role_name)
    )

    existing_role = result.scalar_one_or_none()

    if existing_role:
        raise HTTPException(status_code=404, detail=f"Role '{role_name}' already exists")

    # Create a new role if it doesn't exist
    new_role = Role(name=role_name)
    db.add(new_role)
    await db.commit()  # Commit the transaction asynchronously
    await db.refresh(new_role)  # Refresh to get the role ID or other generated fields
    return new_role


async def delete_role(db: AsyncSession, role_id: uuid.UUID):
    result = await db.execute(
        select(Role).filter(Role.id == role_id)
    )
    role = result.scalar_one_or_none()

    if role:
        await db.delete(role)
        await db.commit()
        return True

    return False


async def add_role_to_user(db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    result = await db.execute(select(Role).filter(Role.id == role_id))
    role = result.scalar_one_or_none()
    if user and role:
        user.role = role
        await db.commit() 
        return True
    return False


async def remove_role_from_user(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user and user.role_id:
        user.role_id = None
        await db.commit()
        return True
    
    return False


async def create_permission(db: AsyncSession, permission_name: str):
    permission = Permission(name=permission_name)
    try:
        db.add(permission)
        await db.commit()  # Commit asynchronously
        await db.refresh(permission)  # Refresh asynchronously to get the latest state of the object
    except Exception as e:
        db.rollback()  # Rollback in case of an error
        raise e
    return permission


async def delete_permission(db: AsyncSession, permission_id: uuid.UUID):
    result = await db.execute(
        select(Permission).filter(Permission.id == permission_id)
    )
    
    permission = result.scalar_one_or_none()
    
    if permission:
        await db.delete(permission)
        await db.commit()
        return True
    return False


async def add_permissions_to_role(db: AsyncSession, role_id: uuid.UUID, permission_ids: list[uuid.UUID]) -> int:
    # Fetch the role and eagerly load permissions to avoid lazy loading issues
    result = await db.execute(select(Role).filter(Role.id == role_id).options(joinedload(Role.permissions)))
    role = result.scalars().first()

    if not role:
        print(f"Role with ID {role_id} not found.")
        return 0  # Return 0 if the role is not found

    added_count = 0

    # Loop through each permission and try to add it to the role
    for permission_id in permission_ids:
        result = await db.execute(select(Permission).filter(Permission.id == permission_id))
        permission = result.scalars().first()

        if not permission:
            print(f"Permission with ID {permission_id} not found.")
            continue  # Skip this permission if not found

        # Check if the permission is already assigned to the role
        if permission not in role.permissions:
            role.permissions.append(permission)
            added_count += 1
        else:
            print(f"Permission {permission_id} already exists for role {role_id}.")

    if added_count > 0:
        await db.commit()  # Commit only if permissions were added
    else:
        print(f"No new permissions were added to role {role_id}.")
    
    return added_count  # Return the count of added permissions






async def remove_permissions_from_role(db: AsyncSession, role_id: uuid.UUID, permission_ids: list):
    # Use `select` for async queries
    result = await db.execute(select(Role).options(joinedload(Role.permissions)).filter(Role.id == role_id))
    role = result.scalars().first()  # Get the first result, if any
    
    if role:
        for permission_id in permission_ids:
            permission_result = await db.execute(select(Permission).filter(Permission.id == permission_id))
            permission = permission_result.scalars().first()
            
            if permission and permission in role.permissions:
                role.permissions.remove(permission)
        
        # Commit the changes
        await db.commit()
        return True
    return False




# A Function That Adds Permissions or a Single Permission to a role
async def add_permissions_to_user(db: AsyncSession, user_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> int:
    # Use execute for async queries
    result = await db.execute(select(User).options(joinedload(User.permissions)).filter(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        return 0  # Return 0 if user is not found

    added_count = 0

    # Add each permission to the role
    for permission_id in permission_ids:
        permission_result = await db.execute(select(Permission).filter(Permission.id == permission_id))
        permission = permission_result.scalars().first()
        
        if permission and permission not in user.permissions:
            user.permissions.append(permission)
            added_count += 1  # Increment count for each permission added

    await db.commit()  # Await commit for async sessions
    return added_count  # Return the count of added permissions




# A Function That Revokes Permission From A User
async def remove_permissions_from_user(db: AsyncSession, user_id: uuid.UUID, permission_ids: list):
    # Use execute for async queries
    result = await db.execute(select(User).options(joinedload(User.permissions)).filter(User.id == user_id))
    user = result.scalars().first()
    
    if user:
        # Load all permissions in a single query
        permission_results = await db.execute(select(Permission).filter(Permission.id.in_(permission_ids)))
        permissions_to_revoke = permission_results.scalars().all()
        
        # Remove permissions from user
        for permission in permissions_to_revoke:
            if permission in user.permissions:
                user.permissions.remove(permission)
        
        await db.commit()  # Await commit for async sessions
        return True
    return False