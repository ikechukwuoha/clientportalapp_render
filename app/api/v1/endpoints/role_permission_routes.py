from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.api.database.db import get_db
from app.api.models.role import Role
from app.api.schemas.role_permission_schema import (
    PermissionAssignment,
    RoleCreate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    RoleAssignment,
    PermissionRevoke
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models.user_model import User
from app.api.models.permission import Permission
from app.api.dependencies.dependencies import get_role_name, get_role_by_name, verify_role_for_admin_or_super_admin
from app.api.security.security import get_current_user_id
from app.api.services.role_permission_services import (
    add_permissions_to_user,
    create_role,
    delete_role,
    add_role_to_user,
    remove_permissions_from_user,
    remove_role_from_user,
    create_permission,
    delete_permission,
    add_permissions_to_role,
    remove_permissions_from_role
)
from sqlalchemy.future import select
import uuid

router = APIRouter()




# Create Role
@router.post("/create-role", tags=["role_permission"])
async def create_new_role(role: RoleCreate, db: AsyncSession = Depends(get_db)):
    created_role = await create_role(db, role.name)
    return {"message": f"Role '{created_role.name}' created successfully.", "role": created_role}



# Delete a role
@router.delete("/delete-role/{role_id}", response_model=dict, tags=["role_permission"])
async def delete_existing_role(role_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    success = await delete_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found.")
    return {"message": "Role deleted successfully."}



# Add a role to a user
@router.post("/add-role-to-user/{user_id}", tags=["role_permission"])
async def assign_role_to_user(user_id: uuid.UUID, role_assignment: RoleAssignment, db: AsyncSession = Depends(get_db)):
    success = await add_role_to_user(db, user_id, role_assignment.role_id)
    if not success:
        raise HTTPException(status_code=404, detail="User or role not found.")
    return {"message": "Role assigned to user successfully."}


# Delete Role from a User
@router.delete("/remove-role-from-user/{user_id}", tags=["role_permission"])
async def revoke_role_from_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    success = await remove_role_from_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User or role not found.")
    return {"message": "Role removed from user successfully."}



# Create a new permission
@router.post("/create-permission", response_model=PermissionResponse, tags=["role_permission"])
async def create_new_permission(permission: PermissionCreate, db: AsyncSession = Depends(get_db)):
    created_permission = await create_permission(db, permission.name)
    
    return PermissionResponse(
        id=created_permission.id,
        name=created_permission.name,
        message=f"Permission '{created_permission.name}' created successfully."
    )



# Delete a permission
@router.delete("/delete-permission/{permission_id}", response_model=dict, tags=["role_permission"])
async def delete_existing_permission(permission_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    success = await delete_permission(db, permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found.")
    return {"message": "Permission deleted successfully."}




# Add multiple permissions to a role
@router.post("/roles/{role_id}/permissions/", tags=["role_permission"])
async def assign_single_or_multiple_permissions_to_role(
    role_id: uuid.UUID,
    permission_ids: list[uuid.UUID],
    db: AsyncSession = Depends(get_db)
):
    added_permissions_count = await add_permissions_to_role(db, role_id, permission_ids)
    
    if added_permissions_count == 0:
        raise HTTPException(status_code=404, detail="Role not found or no new permissions added.")
    
    # Use a clear message based on the number of permissions added
    if added_permissions_count == 1:
        return {"message": "1 permission added to the role successfully."}
    else:
        return {"message": f"{added_permissions_count} permissions added to the role successfully."}


    
    

@router.delete("/permission/{role_id}", tags=["role_permission"])
async def revoke_permissions_from_role(role_id: uuid.UUID, permission_revoke: PermissionRevoke, db: AsyncSession = Depends(get_db)):
    success = await remove_permissions_from_role(db, role_id, permission_revoke.permission_ids)
    
    if not success:
        raise HTTPException(status_code=404, detail="Role or permissions not found.")
    
    return {"message": "Specified permissions removed from the role successfully."}




# Add multiple permissions to a user
@router.post("/user-permissions/{user_id}/permissions", tags=["role_permission"])
async def assign_single_or_multiple_permissions_to_user(
    user_id: uuid.UUID,
    permission_ids: list[uuid.UUID],
    db: Session = Depends(get_db)
):
    added_permissions_count = await add_permissions_to_user(db, user_id, permission_ids)
    print(added_permissions_count)
    
    if added_permissions_count == 0:
        raise HTTPException(status_code=404, detail="User Does not Exist and no new permissions added.")
    
    # Use a clear message based on the number of permissions added
    if added_permissions_count == 1:
        return {"message": "1 permission added to the role successfully."}
    else:
        return {"message": f"{added_permissions_count} permissions added to the user successfully."}
    
    
    

# Remove a permission or multiple permissions from a user
@router.delete("/remove-user-permission/{role_id}", tags=["role_permission"])
async def revoke_permissions_from_user(user_id: uuid.UUID, permission_revoke: PermissionRevoke, db: AsyncSession = Depends(get_db)):
    success = await remove_permissions_from_user(db, user_id, permission_revoke.permission_ids)
    
    if not success:
        raise HTTPException(status_code=404, detail="Role or permissions not found.")
    
    return {"message": "User Permission revoked successfully."}




# A Function to get all Functions
@router.get("/all-permissions", tags=["role_permission"])
async def get_all_permissions(db: AsyncSession = Depends(get_db)):
    permissions = db.query(Permission).all()
    
    return permissions




# A Function to get all Roles
@router.get("/all-roles", tags=["role_permission"])
async def get_all_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role))  # Correct async query
    roles = result.scalars().all()  # Extract roles

    return roles