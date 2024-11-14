from pydantic import BaseModel
import uuid
from typing import List
from sqlalchemy import UUID





class RoleAssignment(BaseModel):
    role_id: uuid.UUID
    
    

class RoleBase(BaseModel):
    name: str
    

class RoleCreate(RoleBase):
    name: str
    


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True





class PermissionBase(BaseModel):
    name: str
    

class PermissionAssignment(BaseModel):
    permission_ids: List[uuid.UUID]

class PermissionCreate(RoleBase):
    name: str


class PermissionRevoke(BaseModel):
    permission_ids: List[uuid.UUID]


class PermissionResponse(RoleBase):
    id: uuid.UUID
    name: str
    message: str

    class Config:
        from_attributes = True