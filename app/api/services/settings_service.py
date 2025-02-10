import uuid
import os
import shutil
from typing import List
from fastapi import UploadFile, File, Form
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update
from sqlalchemy.orm import Session
from pydantic import EmailStr, UUID4
from sqlalchemy.future import select
from app.api.database.db import get_db  # Import your database session
from app.api.models.user_model import User
from fastapi import HTTPException, Depends
from app.api.models.card_model import Card
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.user_schema import UserResponse, UserUpdate  # Import the Pydantic schema
from app.api.schemas.card_schema import CardCreate, CardUpdate, CardResponse

# UPLOAD_DIR = "uploads/profile_pictures"

# async def settings_update_user(
#     user_id: uuid.UUID,
#     file: UploadFile = File(None),  # Optional profile picture
#     first_name: str = Form(None),
#     last_name: str = Form(None),
#     country: str = Form(None),
#     email: EmailStr = Form(None),
#     role_id: UUID4 = Form(None),
#     is_active: bool = Form(None),
#     db: AsyncSession = Depends(get_db)
# ):
#     # Fetch user from the database
#     result = await db.execute(select(User).filter(User.id == user_id))
#     user = result.scalars().first()

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Update user fields if provided
#     if first_name is not None:
#         user.first_name = first_name
#     if last_name is not None:
#         user.last_name = last_name
#     if country is not None:
#         user.country = country
#     if email is not None:
#         user.email = email
#     if role_id is not None:
#         user.role_id = role_id
#     if is_active is not None:
#         user.is_active = is_active

#     # Handle file upload if a file is provided
#     if file:
#         os.makedirs(UPLOAD_DIR, exist_ok=True)
#         file_location = f"{UPLOAD_DIR}/{user_id}_{file.filename}"
#         with open(file_location, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#         user.profile_picture = file_location

#     await db.commit()
#     await db.refresh(user)

#     return {
#         "message": "User updated successfully",
#         "user": {
#             "id": str(user.id),
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "country": user.country,
#             "email": user.email,
#             "role_id": str(user.role_id) if user.role_id else None,
#             "is_active": user.is_active,
#             "profile_picture_url": user.profile_picture
#         }
#     }

# async def update_user(user_id: uuid.UUID, user_update: UserUpdate, db: AsyncSession):
#     result = await db.execute(select(User).filter(User.id == user_id))  
#     user = result.scalars().first()

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Update only provided fields
#     update_data = {key: value for key, value in user_update.model_dump(exclude_unset=True).items() if value != ""}
    
#     for key, value in update_data.items():
#         setattr(user, key, value)

#     await db.commit()
#     await db.refresh(user)

#     return user

async def update_user(user_id: uuid.UUID, user_update: UserUpdate, db: AsyncSession):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)
    #return user

# If using Pydantic model:


async def settings_create_card(user_id: uuid.UUID, card_data: CardCreate, db: AsyncSession):
    # Ensure the user exists
    user_result = await db.execute(select(User).filter(User.id == user_id))
    user = user_result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Normalize card number (trim spaces and compare in lowercase)
    card_number_clean = card_data.card_number.strip().lower()

    # Check if the card number already exists (case-insensitive)
    existing_card = await db.execute(
        select(Card).filter(Card.card_number.ilike(card_number_clean))
    )
    
    if existing_card.scalars().first():
        raise HTTPException(status_code=400, detail="Card number already exists")

    # Prepare card data dictionary and override card_number
    card_data_dict = card_data.model_dump()
    card_data_dict["card_number"] = card_number_clean  # Override with cleaned value

    # Assign user_id explicitly
    new_card = Card(**card_data_dict, user_id=user_id)

    try:
        db.add(new_card)
        await db.commit()
        await db.refresh(new_card)
        return new_card
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Card number must be unique")


async def settings_get_user_cards(user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Card).filter(Card.user_id == user_id))
    cards = result.scalars().all()
    return cards

async def settings_get_user_card(card_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Card).filter(Card.id == card_id))
    card = result.scalars().first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return card

async def settings_update_card(card_id: uuid.UUID, card_update: CardUpdate, db: AsyncSession):
    # Fetch the existing card
    result = await db.execute(select(Card).filter(Card.id == card_id))
    card = result.scalars().first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Get only the non-empty values from the update request
    update_data = {key: value for key, value in card_update.model_dump(exclude_unset=True).items() if value != ""}

    # Check if the update request is setting a new default card
    if update_data.get("is_default", False):  # If is_default is being set to True
        # Unset all other default cards for the same user
        await db.execute(
            update(Card)
            .where(Card.user_id == card.user_id, Card.id != card.id)
            .values(is_default=False)
        )

    # Apply updates to the card
    for key, value in update_data.items():
        setattr(card, key, value)

    # Commit the changes
    await db.commit()
    await db.refresh(card)
    return card

async def settings_delete_card(user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Card).filter(Card.id == user_id))
    card = result.scalars().first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    await db.delete(card)
    await db.commit()
    return {"message": "Card deleted successfully"}                               


# async def settings_create_card(user_id: uuid.UUID, card_data: CardCreate, db: AsyncSession):
#     # Ensure the user exists
#     user_result = await db.execute(select(User).filter(User.id == user_id))
#     user = user_result.scalars().first()
    
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     new_card = Card(**card_data.model_dump())
#     db.add(new_card)
#     await db.commit()
#     await db.refresh(new_card)
#     return new_card