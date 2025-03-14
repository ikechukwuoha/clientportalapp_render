# import uuid
# from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, JSON
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from app.api.models import Base
# from sqlalchemy.dialects.postgresql import UUID
# from datetime import datetime, timezone
# from uuid import uuid4


# class SiteData(Base):
#     __tablename__ = "site_data"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
#     site_name = Column(String, nullable=False)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

#     # Totals data
#     total_users_count = Column(Integer)
#     active_users_count = Column(Integer)
#     active_modules_count = Column(Integer)
#     active_sites = Column(Integer)

#     # Storing additional data as JSON
#     total_users = Column(JSON)
#     active_users = Column(JSON)
#     active_modules = Column(JSON)
#     sites_data = Column(JSON)
    
    

#     creation_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
#     updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#     # Relationships
#     user = relationship("User", back_populates="site_data")






from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.api.models import Base
import uuid
from datetime import datetime, timezone


class SiteData(Base):
    __tablename__ = "site_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    site_name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Totals data
    total_users_count = Column(Integer)
    active_users_count = Column(Integer)
    active_modules_count = Column(Integer)
    total_site_counts =  Column(Integer)
    active_site_counts =  Column(Integer)
    
    #site active status
    active_sites = Column(Boolean, default=False)

    # Storing additional data as JSON
    total_users = Column(JSON)
    active_users = Column(JSON)
    active_modules = Column(JSON)
    sites_data = Column(JSON)

    location = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="site_data")
