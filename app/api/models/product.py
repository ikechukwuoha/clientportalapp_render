# import uuid
# from sqlalchemy import Column, Float, String, DateTime, Boolean, Integer, ForeignKey, Text, JSON
# from sqlalchemy.sql import func
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import relationship
# from app.api.models import Base
# from uuid import uuid4




# class Product(Base):
#     __tablename__ = "products"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
#     product_title = Column(String, nullable=False) 
#     product_code = Column(String, unique=True, nullable=False) 
#     item_group = Column(String, nullable=False)
#     product_description = Column(Text, nullable=False)
#     product_image = Column(String, nullable=False)

#     # JSON fields to store nested data
#     benefits = Column(JSON, nullable=True)
#     images = Column(JSON, nullable=True)
#     plan_descriptions = Column(JSON, nullable=True)
#     prices = Column(JSON, nullable=True)

#     created_at = Column(DateTime, server_default=func.now(), nullable=False)
#     updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)





import uuid
from sqlalchemy import Column, Float, String, DateTime, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.api.models import Base
from uuid import uuid4


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_title = Column(String, nullable=False) 
    product_code = Column(String, unique=True, nullable=False) 
    item_group = Column(String, nullable=False)
    product_description = Column(Text, nullable=False)
    product_image = Column(String, nullable=False)

    # JSON fields to store nested data
    benefits = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True)
    plans = Column(JSON, nullable=True)  # This replaces plan_descriptions and prices

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)