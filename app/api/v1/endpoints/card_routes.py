#The Handles The Routing For All User Logic
import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Response
from app.api.database.db import get_db
from app.api.schemas.card_schema import CardCreate, CardResponse, CardUpdate
from app.api.services.settings_service import settings_create_card, settings_get_user_cards, settings_get_user_card, settings_update_card, settings_delete_card
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()
@router.post("/initialize-card/{user_id}", status_code=status.HTTP_200_OK, tags=['card'])
async def create_card(user_id: uuid.UUID, create_card: CardCreate, db: AsyncSession = Depends(get_db)):
    return await settings_create_card(user_id, create_card, db)

@router.get("/get-user-cards/{user_id}", response_model=List[CardResponse], tags=['card'])
async def get_user_cards(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await settings_get_user_cards(user_id, db)

@router.get("/get-card/{card_id}",response_model=CardResponse, tags=['card'])
async def get_card(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await settings_get_user_card(card_id, db)

@router.put("/update-card/{card_id}", response_model=CardResponse, tags=['card'])
async def update_card(card_id: uuid.UUID, update_card: CardUpdate, db: AsyncSession = Depends(get_db)):
    return await settings_update_card(card_id, update_card, db)

@router.delete("/delete-card/{card_id}", tags=['card'])
async def delet_card(card_id:uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await settings_delete_card(card_id, db)