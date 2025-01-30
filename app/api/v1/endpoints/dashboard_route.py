from fastapi import APIRouter, Depends, Query
from app.api.services.dashboard_services import fetch_total_users, fetch_active_users, fetch_active_modules, fetch_active_sites, fetch_active_users_dynamic, fetch_user_data, fetch_user_data_count, get_site_data
from sqlalchemy import select
from app.api.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException





router = APIRouter()

@router.get("/get-total-users", tags=["dashboard"])
async def get_total_users():
    """
    Get total users
    """
    return await fetch_total_users()

@router.get("/get-active-users", tags=["dashboard"])
async def get_active_users():
    """
    Get Active users
    """
    return await fetch_active_users()

@router.get("/get-active-users-dynamic", tags=["dashboard"])
async def get_active_users_dynamic(email: str = Query(..., description="The email to filter sites")):
    """
    Get Active users
    """
    return await fetch_active_users_dynamic(email=email)

@router.get("/get-active-modules", tags=["dashboard"])
async def get_active_modules():
    """
    Get Active modules
    """
    return await fetch_active_modules()

@router.get("/get-sites", tags=["dashboard"])
async def get_active_site(email: str = Query(..., description="The email to filter sites")):
    """
    Get Sites
    """
    return await fetch_active_sites(email=email)

@router.get("/get-overview", tags=["dashboard"])
async def get_overview_data(email: str = Query(..., description="The email to filter sites"),  db: AsyncSession = Depends(get_db)):
    """
    Get Data
    """
    return await fetch_user_data(email=email, db=db)

@router.get("/get-overview-count", tags=["dashboard"])
async def get_overview_count(email: str = Query(..., description="The email to filter Data")):
    """
    Get Data
    """
    return await fetch_user_data_count(email=email)






@router.get("/sites-data", tags=["dashboard"])
async def fetch_site_data(id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch site data for the given user ID.
    """
    if not id:
        raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

    try:
        data = await get_site_data(id=id, db=db)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
