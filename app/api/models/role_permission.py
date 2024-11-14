from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.api.models import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID





# Association table for roles and permissions
role_permissions = Table(
    'role_permissions', Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)



# Association table for User and Permission (many-to-many)
user_permissions = Table(
    'user_permissions', Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)