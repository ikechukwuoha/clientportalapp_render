
import asyncio
import datetime
from socket import timeout
from fastapi import APIRouter, Depends, Query, HTTPException
from app.api.models.site_data import SiteData
from app.api.services.dashboard_services import fetch_total_users, fetch_active_users, fetch_active_modules, fetch_active_sites, fetch_active_users_dynamic, fetch_user_data, fetch_user_data_count, get_site_data
from sqlalchemy import select
from app.api.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Dict, Any
import logging
from sqlalchemy.orm import selectinload



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



@router.post("/webhook/user-update")
async def handle_user_webhook(
    payload: Dict[str, Any], 
    db: AsyncSession = Depends(get_db)
):
    try:
        # Validate required fields in payload
        if not all(key in payload for key in ["site_name", "data"]):
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: site_name and data"
            )

        site_name = payload["site_name"]
        data = payload["data"]

        # Validate data structure
        required_data_fields = ["total_users", "active_users"]
        if not all(key in data for key in required_data_fields):
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required data fields: {required_data_fields}"
            )

        # Fetch existing site data with a timeout
        async with timeout(10):  # 10 seconds timeout
            result = await db.execute(
                select(SiteData)
                .filter(SiteData.site_name == site_name)
                .options(selectinload(SiteData.user))  # If you have relationships
            )
            site_data = result.scalar_one_or_none()

        if not site_data:
            raise HTTPException(
                status_code=404,
                detail=f"Site {site_name} not found in database"
            )

        # Update site data with new user information
        try:
            site_data.total_users = data["total_users"]["users"]
            site_data.total_users_count = data["total_users"]["count"]
            site_data.active_users = data["active_users"]["users"]
            site_data.active_users_count = data["active_users"]["count"]

            # Update the sites_data dictionary
            site_data.sites_data.update({
                "total_users": data["total_users"],
                "active_users": data["active_users"]
            })

            # Update last_updated timestamp if you have one
            site_data.last_updated = datetime.utcnow()

            await db.commit()

            # Log successful update
            logging.info(f"Successfully updated site data for {site_name}")

            return {
                "status": "success",
                "message": "Site data updated successfully",
                "site_name": site_name,
                "updated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            await db.rollback()
            logging.error(f"Error updating site data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error updating site data: {str(e)}"
            )

    except asyncio.TimeoutError:
        await db.rollback()
        logging.error(f"Timeout while processing webhook for site {site_name}")
        raise HTTPException(
            status_code=504,
            detail="Request timed out"
        )
    except Exception as e:
        await db.rollback()
        logging.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )