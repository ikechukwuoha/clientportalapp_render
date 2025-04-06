
import asyncio
from datetime import datetime
import json
from socket import timeout
from fastapi import APIRouter, Depends, Query, HTTPException, Request, logger
from app.api.models.site_data import SiteData
from app.api.models.user_model import User
from app.api.services.dashboard_services import fetch_total_users, fetch_active_users, fetch_active_modules, fetch_active_sites, fetch_active_users_dynamic, fetch_user_data, fetch_user_data_count, get_site_data
from sqlalchemy import select
from app.api.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import and_ 


from typing import Dict, Any
import logging
from sqlalchemy.orm import selectinload

from sqlalchemy.orm import Session

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)



def get_site_base_data(site):
    """Helper function to get basic site data from database."""
    return {
        "site_name": site.site_name,
        "active": site.active_sites,
        "creation_date": site.created_at,
        "country": site.location,
    }

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
    except TypeError as e:
        if "got an unexpected keyword argument 'id'" in str(e):
            return {
                "status": "error",
                "message": "This user has not Purchased any Erp Plan Yet"
            }
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



    
    
    

@router.post("/webhook/site-data")
async def receive_site_data(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receives consolidated site data from the webhook, updates or creates corresponding
    SiteData records, deletes sites not present in the webhook, and commits changes.
    """
    try:
        # Parse JSON payload
        data = await request.json()
        logger.info(f"Received webhook: {data}")

        # Check for success status in payload
        if data.get("status") != "success":
            error_msg = data.get("message", "Unknown error")
            logger.error(f"Error in webhook data: {error_msg}")
            return {"status": "error", "message": f"Received error data: {error_msg}"}

        # Extract email from first site's site_info
        sites_data = data.get("data", {}).get("sites_data", [])
        email = None
        if sites_data and "site_info" in sites_data[0]:
            email = sites_data[0]["site_info"].get("email")
        if not email:
            logger.error("Email not found in webhook data")
            return {"status": "error", "message": "Email not found in data"}

        # Fetch user from database using the email
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            logger.warning(f"No user found for email: {email}")
            return {"status": "error", "message": f"No user found for email: {email}"}

        # Get incoming site names
        incoming_site_names = {site.get("site_info", {}).get("site_name") for site in sites_data if site.get("site_info", {}).get("site_name")}

        # Find and delete sites not in the incoming data
        result = await db.execute(
            select(SiteData).filter(
                and_(
                    SiteData.user_id == user.id,
                    SiteData.site_name.notin_(incoming_site_names)
                )
            )
        )
        sites_to_delete = result.scalars().all()
        
        deleted_sites_count = 0
        for site in sites_to_delete:
            await db.delete(site)
            deleted_sites_count += 1
            logger.info(f"Deleted site not present in webhook: {site.site_name}")

        # Process each site data entry (update or create)
        totals = data.get("data", {}).get("totals", {})
        total_sites_count = totals.get("total_sites", 0)
        active_sites_count = totals.get("active_sites", 0)

        updated_sites = 0

        for site in sites_data:
            site_info = site.get("site_info", {})
            stats = site.get("stats", {})
            site_name = site_info.get("site_name")
            site_status = site_info.get("site_status")
            country = site_info.get("country")

            if not site_name:
                logger.error("Site name missing in site data")
                continue

            # Check if the site already exists in the database
            result = await db.execute(select(SiteData).filter(SiteData.site_name == site_name))
            existing_site = result.scalar_one_or_none()

            if existing_site:
                # Update the existing site's stats and info
                existing_site.total_users_count = stats.get("total_users", 0)
                existing_site.active_users_count = stats.get("active_users", 0)
                existing_site.active_modules_count = stats.get("active_modules", 0)
                existing_site.active_sites = site_status
                existing_site.location = country 
                existing_site.total_users = stats.get("users", [])
                existing_site.active_users = stats.get("active_users_list", [])
                existing_site.active_modules = stats.get("modules", [])
                existing_site.sites_data = site  # Store full site data
                existing_site.updated_at = datetime.now()
                existing_site.total_site_counts = total_sites_count
                existing_site.active_site_counts = active_sites_count
                logger.info(f"Updated site: {site_name}")
            else:
                # Create a new SiteData record
                new_site = SiteData(
                    site_name=site_name,
                    active_sites=site_status,
                    location=country,
                    total_users_count=stats.get("total_users", 0),
                    active_users_count=stats.get("active_users", 0),
                    active_modules_count=stats.get("active_modules", 0),
                    total_users=stats.get("users", []),
                    active_users=stats.get("active_users_list", []),
                    active_modules=stats.get("modules", []),
                    sites_data=site,
                    user_id=user.id,
                    total_site_counts=total_sites_count,
                    active_site_counts=active_sites_count
                )
                db.add(new_site)
                logger.info(f"Created new site: {site_name}")

            updated_sites += 1

        # Commit the database changes
        await db.commit()

        # Refresh each site record to ensure latest state is loaded
        for site in sites_data:
            site_name = site.get("site_info", {}).get("site_name")
            if site_name:
                result = await db.execute(select(SiteData).filter(SiteData.site_name == site_name))
                refreshed_site = result.scalar_one_or_none()
                if refreshed_site:
                    await db.refresh(refreshed_site)

        # Log summary information
        logger.info(f"Site Data Summary - Email: {email}, "
                    f"Updated Sites: {updated_sites}, "
                    f"Deleted Sites: {deleted_sites_count}, "
                    f"Total Sites (from payload): {total_sites_count}, "
                    f"Active Sites (from payload): {active_sites_count}")

        return {
            "status": "success",
            "message": f"Updated {updated_sites} sites, deleted {deleted_sites_count} sites for user {email}",
            "updated_sites": updated_sites,
            "deleted_sites": deleted_sites_count
        }

    except Exception as e:
        logger.exception("An error occurred while processing the webhook data")
        return {"status": "error", "message": str(e)}






@router.get("/active-modules", tags=["destructured dashboard data"])
async def get_active_modules(
    id: str = Query(..., description="User ID to fetch active modules for"),
    date: str = Query(None, description="Date filter (e.g., 'Last 7 days')"),
    search: str = Query(None, description="Search term to filter modules"),
    db: AsyncSession = Depends(get_db)
):
    """Fetch active modules data from database."""
    if not id:
        raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

    try:
        result = await db.execute(select(SiteData).where(SiteData.user_id == id))
        user_sites = result.scalars().all()

        if not user_sites:
            return {
                "total_active_modules": 0,
                "modules_by_site": []
            }

        modules_data = []
        total_active_modules = 0

        for site in user_sites:
            modules_count = site.active_modules_count or 0
            total_active_modules += modules_count

            # Check if the search term matches the site name
            site_name_matches = False
            if search and search.lower() in site.site_name.lower():
                site_name_matches = True

            # Filter modules based on the search term
            filtered_modules = []
            if search:
                for module in site.active_modules or []:
                    if (
                        search.lower() in module.get("module_name", "").lower()
                        or search.lower() in module.get("app_name", "").lower()
                        or site_name_matches  # Include all modules if site name matches
                    ):
                        filtered_modules.append(module)
            else:
                filtered_modules = site.active_modules or []

            # Only include sites that match the search or have matching modules
            if not search or filtered_modules or site_name_matches:
                modules_data.append({
                    "site_name": site.site_name,
                    "active_modules": {
                        "count": len(filtered_modules),
                        "modules": filtered_modules
                    }
                })

        return {
            "total_active_modules": total_active_modules,
            "modules_by_site": modules_data
        }

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



    
    
    
    
@router.get("/active-sites-count", tags=["destructured dashboard data"])
async def get_active_sites_count(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch active sites count from database."""
    if not id:
        raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

    try:
        result = await db.execute(select(SiteData).where(SiteData.user_id == id))
        user_sites = result.scalars().all()

        if not user_sites:
            return {"active_sites_count": 0}

        # Get counts from the first site record
        active_sites_count = user_sites[0].active_site_counts if user_sites else 0
        
        return {"active_sites_count": active_sites_count}

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
    


@router.get("/total-sites-count", tags=["destructured dashboard data"])
async def get_total_sites_count(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch total sites count from database."""
    if not id:
        raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

    try:
        result = await db.execute(select(SiteData).where(SiteData.user_id == id))
        user_sites = result.scalars().all()

        if not user_sites:
            return {"total_sites_count": 0}

        # Get total sites count from the first site record
        total_sites_count = user_sites[0].total_site_counts if user_sites else 0
        
        return {"total_sites_count": total_sites_count}

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
    
    

@router.get("/active-users", tags=["destructured dashboard data"])
async def get_active_users(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch active users data from database."""
    if not id:
        raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

    try:
        result = await db.execute(select(SiteData).where(SiteData.user_id == id))
        user_sites = result.scalars().all()

        if not user_sites:
            return {
                "sites": []
            }

        sites = []

        for site in user_sites:
            sites.append({
                "site_name": site.site_name,
                "users": site.active_users or []
            })

        return {
            "sites": sites
        }

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}") 
    
    

@router.get("/total-users", tags=["destructured dashboard data"])
async def get_total_users(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch total users data from database."""
    if not id:
        raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

    try:
        result = await db.execute(select(SiteData).where(SiteData.user_id == id))
        user_sites = result.scalars().all()

        if not user_sites:
            return {
                "users_by_site": []
            }

        users_data = []

        for site in user_sites:
            users_data.append({
                "site_name": site.site_name,
                "users": site.total_users or []
            })

        return {
            "users_by_site": users_data
        }

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")




@router.get("/site-totals", tags=["destructured dashboard data"])
async def get_site_totals(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch only total sites count from database."""
    if not id:
        raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

    try:
        result = await db.execute(select(SiteData).where(SiteData.user_id == id))
        user_sites = result.scalars().all()

        if not user_sites:
            return {"total_sites": 0}

        # Get total sites count from the first site record
        total_sites_count = user_sites[0].total_site_counts if user_sites else 0
        
        # Return only the total_sites value
        return {"total_sites": total_sites_count}

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
    


@router.get("/active-sites-total", tags=["destructured dashboard data"])
async def get_active_sites_total(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch only active sites count from database."""
    if not id:
        raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

    try:
        result = await db.execute(select(SiteData).where(SiteData.user_id == id))
        user_sites = result.scalars().all()

        if not user_sites:
            return {"active_sites": 0}

        # Get active sites count from the first site record
        active_sites_count = user_sites[0].active_site_counts if user_sites else 0
        
        # Return only the active_sites value
        return {"active_sites": active_sites_count}

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")









# @router.get("/active-modules", tags=["destructured dashboard data"])
# async def get_active_modules(id: str, db: AsyncSession = Depends(get_db)):
#     """Fetch active modules data from database."""
#     if not id:
#         raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

#     try:
#         result = await db.execute(select(SiteData).where(SiteData.user_id == id))
#         user_sites = result.scalars().all()

#         if not user_sites:
#             return {
#                 "total_active_modules": 0,
#                 "modules_by_site": []
#             }

#         modules_data = []
#         total_active_modules = 0

#         for site in user_sites:
#             modules_count = site.active_modules_count or 0
#             total_active_modules += modules_count

#             modules_data.append({
#                 "site_name": site.site_name,  # Only include site name
#                 "active_modules": {
#                     "count": modules_count,
#                     "modules": site.active_modules or []
#                 }
#             })

#         return {
#             "total_active_modules": total_active_modules,
#             "modules_by_site": modules_data
#         }

#     except Exception as e:
#         logging.error(f"Database error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# @router.post("/webhook/site-data")
# async def receive_site_data(request: Request, db: AsyncSession = Depends(get_db)):
#     try:
#         # Parse JSON payload
#         data = await request.json()
#         logger.info(f"Received webhook data: {data}")
        
#         # Extract webhook data based on structure
#         webhook_data = None
#         email = None
        
#         # First structure: data contains status and data fields
#         if "status" in data:
#             if data.get("status") != "success":
#                 error_msg = data.get("message", "Unknown error")
#                 logger.error(f"Error in webhook data: {error_msg}")
#                 return {"status": "error", "message": f"Received error data: {error_msg}"}
                
#             webhook_data = data.get("data", {})
#             email = webhook_data.get("email")
            
#         # Second structure: data nested under message
#         elif "message" in data:
#             message = data.get("message", {})
#             if message.get("status") != "success":
#                 error_msg = message.get("message", "Unknown error")
#                 logger.error(f"Error in webhook data: {error_msg}")
#                 return {"status": "error", "message": f"Received error data: {error_msg}"}
                
#             webhook_data = message.get("data", {})
#             email = webhook_data.get("email")
            
#         else:
#             logger.error("Invalid webhook data structure")
#             return {"status": "error", "message": "Invalid webhook data structure"}
        
#         # Validate email presence
#         if not email:
#             logger.error("Email not found in webhook data")
#             return {"status": "error", "message": "Email not found in data"}
        
#         # Fetch user from the database
#         result = await db.execute(select(User).filter(User.email == email))
#         user = result.scalar_one_or_none()
        
#         if not user:
#             logger.warning(f"No user found for email: {email}")
#             return {"status": "error", "message": f"No user found for email: {email}"}
        
#         # Process sites data
#         totals = webhook_data.get("totals", {})
#         sites_data = webhook_data.get("sites_data", [])
#         updated_sites = 0
        
#         if not sites_data:
#             logger.error("No sites data found in webhook payload")
#             return {"status": "error", "message": "No sites data found"}
        
#         for site in sites_data:
#             site_info = site.get("site_info", {})
#             site_name = site_info.get("site_name")
#             site_status = site_info.get("site_status")
            
#             if not site_name or not site_status:
#                 logger.error(f"Missing site_name or site_status in site data: {site}")
#                 continue
            
#             # Check if site exists in the database
#             existing_site = await db.execute(
#                 select(SiteData).filter(SiteData.site_name == site_name)
#             )
#             existing_site = existing_site.scalar_one_or_none()
            
#             if existing_site:
#                 # Update existing site
#                 existing_site.total_users_count = site.get("stats", {}).get("total_users", 0)
#                 existing_site.active_users_count = site.get("stats", {}).get("active_users", 0)
#                 existing_site.active_modules_count = site.get("stats", {}).get("active_modules", 0)
#                 existing_site.active_sites = site_status
#                 existing_site.total_users = site.get("stats", {}).get("users", [])
#                 existing_site.active_users = site.get("stats", {}).get("active_users_list", [])
#                 existing_site.active_modules = site.get("stats", {}).get("modules", [])
#                 existing_site.sites_data = site
#                 existing_site.updated_at = datetime.now()
#                 updated_sites += 1
#             else:
#                 # Create new site
#                 new_site = SiteData(
#                     site_name=site_name,
#                     active_sites=site_status,
#                     total_users_count=site.get("stats", {}).get("total_users", 0),
#                     active_users_count=site.get("stats", {}).get("active_users", 0),
#                     active_modules_count=site.get("stats", {}).get("active_modules", 0),
#                     total_users=site.get("stats", {}).get("users", []),
#                     active_users=site.get("stats", {}).get("active_users_list", []),
#                     active_modules=site.get("stats", {}).get("modules", []),
#                     sites_data=site,
#                     user_id=user.id
#                 )
#                 db.add(new_site)
#                 updated_sites += 1
        
#         # Commit changes to the database
#         await db.commit()
        
#         # Log summary
#         logger.info(f"📊 Site Data Summary:")
#         logger.info(f"  Email: {email}")
#         logger.info(f"  Updated Sites: {updated_sites}")
#         logger.info(f"  Total Sites: {totals.get('total_sites', 0)}")
#         logger.info(f"  Active Sites: {totals.get('active_sites', 0)}")
        
#         return {
#             "status": "success", 
#             "message": f"Updated {updated_sites} sites for user {email}",
#             "updated_sites": updated_sites
#         }
    
#     except Exception as e:
#         logger.error(f"An error occurred: {e}")
#         await db.rollback()
#         return {"status": "error", "message": str(e)}






# @router.post("/webhook/site-data")
# async def receive_site_data(request: Request, db: AsyncSession = Depends(get_db)):
#     try:
#         # Parse JSON payload
#         data = await request.json()
#         logger.info(f"Received webhook data: {data}")
        
#         # Check if the webhook status is successful
#         message = data.get("message", {})
#         if message.get("status") != "success":
#             error_msg = message.get("message", "Unknown error")
#             logger.error(f"Error in webhook data: {error_msg}")
#             return {"status": "error", "message": f"Received error data: {error_msg}"}
        
#         # Extract email from the data
#         webhook_data = message.get("data", {})
#         email = webhook_data.get("email")
#         if not email:
#             logger.error("Email not found in webhook data")
#             return {"status": "error", "message": "Email not found in data"}
        
#         # Fetch user from the database
#         result = await db.execute(select(User).filter(User.email == email))
#         user = result.scalar_one_or_none()
        
#         if not user:
#             logger.warning(f"No user found for email: {email}")
#             return {"status": "error", "message": f"No user found for email: {email}"}
        
#         # Process sites data
#         totals = webhook_data.get("totals", {})
#         sites_data = webhook_data.get("sites_data", [])
#         updated_sites = 0
        
#         if not sites_data:
#             logger.error("No sites data found in webhook payload")
#             return {"status": "error", "message": "No sites data found"}
        
#         for site in sites_data:
#             site_info = site.get("site_info", {})
#             site_name = site_info.get("site_name")
#             site_status = site_info.get("site_status")
            
#             if not site_name or not site_status:
#                 logger.error(f"Missing site_name or site_status in site data: {site}")
#                 continue
            
#             # Check if site exists in the database
#             existing_site = await db.execute(
#                 select(SiteData).filter(SiteData.site_name == site_name)
#             )
#             existing_site = existing_site.scalar_one_or_none()
            
#             if existing_site:
#                 # Update existing site
#                 existing_site.total_users_count = site.get("stats", {}).get("total_users", 0)
#                 existing_site.active_users_count = site.get("stats", {}).get("active_users", 0)
#                 existing_site.active_modules_count = site.get("stats", {}).get("active_modules", 0)
#                 existing_site.active_sites = site_status
#                 existing_site.total_users = site.get("stats", {}).get("users", [])
#                 existing_site.active_users = site.get("stats", {}).get("active_users_list", [])
#                 existing_site.active_modules = site.get("stats", {}).get("modules", [])
#                 existing_site.sites_data = site
#                 existing_site.updated_at = datetime.now()
#                 updated_sites += 1
#             else:
#                 # Create new site
#                 new_site = SiteData(
#                     site_name=site_name,
#                     active_sites=site_status,
#                     total_users_count=site.get("stats", {}).get("total_users", 0),
#                     active_users_count=site.get("stats", {}).get("active_users", 0),
#                     active_modules_count=site.get("stats", {}).get("active_modules", 0),
#                     total_users=site.get("stats", {}).get("users", []),
#                     active_users=site.get("stats", {}).get("active_users_list", []),
#                     active_modules=site.get("stats", {}).get("modules", []),
#                     sites_data=site,
#                     user_id=user.id
#                 )
#                 db.add(new_site)
#                 updated_sites += 1
        
#         # Commit changes to the database
#         await db.commit()
        
#         # Log summary
#         logger.info(f"📊 Site Data Summary:")
#         logger.info(f"  Email: {email}")
#         logger.info(f"  Updated Sites: {updated_sites}")
#         logger.info(f"  Total Sites: {totals.get('total_sites', 0)}")
#         logger.info(f"  Active Sites: {totals.get('active_sites', 0)}")
        
#         return {
#             "status": "success", 
#             "message": f"Updated {updated_sites} sites for user {email}",
#             "updated_sites": updated_sites
#         }
    
#     except Exception as e:
#         logger.error(f"An error occurred: {e}")
#         await db.rollback()
#         return {"status": "error", "message": str(e)}











# @router.post("/webhook/site-data")
# async def receive_site_data(request: Request, db: AsyncSession = Depends(get_db)):
#     # Parse JSON payload
#     data = await request.json()
#     logger.info(f"Received webhook: {data}")
    
#     if data.get("status") != "success":
#         error_msg = data.get("message", "Unknown error")
#         logger.error(f"Error in webhook data: {error_msg}")
#         return {"status": "error", "message": f"Received error data: {error_msg}"}
    
#     # Extract email from first site if available
#     email = None
#     sites_data = data.get("data", {}).get("sites_data", [])
#     if sites_data and "site_info" in sites_data[0]:
#         email = sites_data[0]["site_info"].get("email")
    
#     if not email:
#         logger.error("Email not found in webhook data")
#         return {"status": "error", "message": "Email not found in data"}
    
#     # Fetch user from database
#     result = await db.execute(select(User).filter(User.email == email))
#     user = result.scalar_one_or_none()
    
#     if not user:
#         logger.warning(f"No user found for email: {email}")
#         return {"status": "error", "message": f"No user found for email: {email}"}
    
#     # Process sites data
#     totals = data.get("data", {}).get("totals", {})
#     updated_sites = 0
    
#     for site in sites_data:
#         site_name = site["site_info"]["site_name"]
#         site_status = site["site_info"]["site_status"]
        
#         # Check if site exists
#         existing_site = await db.execute(
#             select(SiteData).filter(SiteData.site_name == site_name)
#         )
#         existing_site = existing_site.scalar_one_or_none()
        
#         if existing_site:
#             # Update existing site
#             existing_site.total_users_count = site["stats"]["total_users"]
#             existing_site.active_users_count = site["stats"]["active_users"]
#             existing_site.active_modules_count = site["stats"]["active_modules"]
#             existing_site.active_sites = site_status
#             existing_site.total_users = site["stats"]["users"]
#             existing_site.active_users = site["stats"]["active_users_list"]
#             existing_site.active_modules = site["stats"]["modules"]
#             existing_site.sites_data = site
#             existing_site.updated_at = datetime.now()
#             updated_sites += 1
#         else:
#             # Create new site
#             new_site = SiteData(
#                 site_name=site_name,
#                 active_sites=site_status,
#                 total_users_count=site["stats"]["total_users"],
#                 active_users_count=site["stats"]["active_users"],
#                 active_modules_count=site["stats"]["active_modules"],
#                 total_users=site["stats"]["users"],
#                 active_users=site["stats"]["active_users_list"],
#                 active_modules=site["stats"]["modules"],
#                 sites_data=site,
#                 user_id=user.id
#             )
#             db.add(new_site)
#             updated_sites += 1
    
#     # Commit changes
#     await db.commit()
    
#     # Refresh the objects to ensure they reflect the latest database state
#     for site in sites_data:
#         site_name = site["site_info"]["site_name"]
#         result = await db.execute(select(SiteData).filter(SiteData.site_name == site_name))
#         refreshed_site = result.scalar_one_or_none()
#         if refreshed_site:
#             await db.refresh(refreshed_site)
    
#     # Log summary
#     print(f"📊 Site Data Summary:")
#     print(f"  Email: {email}")
#     print(f"  Updated Sites: {updated_sites}")
#     print(f"  Total Sites: {totals.get('total_sites', 0)}")
#     print(f"  Active Sites: {totals.get('active_sites', 0)}")
    
#     return {
#         "status": "success", 
#         "message": f"Updated {updated_sites} sites for user {email}",
#         "updated_sites": updated_sites
#     }








# @router.post("/webhook/user-update")
# async def handle_user_webhook(
#     payload: Dict[str, Any], 
#     db: AsyncSession = Depends(get_db)
# ):
#     try:
#         # Validate required fields in payload
#         if not all(key in payload for key in ["site_name", "data"]):
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Missing required fields: site_name and data"
#             )

#         site_name = payload["site_name"]
#         data = payload["data"]

#         # Validate data structure
#         required_data_fields = ["total_users", "active_users"]
#         if not all(key in data for key in required_data_fields):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Missing required data fields: {required_data_fields}"
#             )

#         # Fetch existing site data with a timeout
#         async with timeout(10):  # 10 seconds timeout
#             result = await db.execute(
#                 select(SiteData)
#                 .filter(SiteData.site_name == site_name)
#                 .options(selectinload(SiteData.user))  # If you have relationships
#             )
#             site_data = result.scalar_one_or_none()

#         if not site_data:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Site {site_name} not found in database"
#             )

#         # Update site data with new user information
#         try:
#             site_data.total_users = data["total_users"]["users"]
#             site_data.total_users_count = data["total_users"]["count"]
#             site_data.active_users = data["active_users"]["users"]
#             site_data.active_users_count = data["active_users"]["count"]

#             # Update the sites_data dictionary
#             site_data.sites_data.update({
#                 "total_users": data["total_users"],
#                 "active_users": data["active_users"]
#             })

#             # Update last_updated timestamp if you have one
#             site_data.last_updated = datetime.utcnow()

#             await db.commit()

#             # Log successful update
#             logging.info(f"Successfully updated site data for {site_name}")

#             return {
#                 "status": "success",
#                 "message": "Site data updated successfully",
#                 "site_name": site_name,
#                 "updated_at": datetime.utcnow().isoformat()
#             }

#         except Exception as e:
#             await db.rollback()
#             logging.error(f"Error updating site data: {str(e)}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error updating site data: {str(e)}"
#             )

#     except asyncio.TimeoutError:
#         await db.rollback()
#         logging.error(f"Timeout while processing webhook for site {site_name}")
#         raise HTTPException(
#             status_code=504,
#             detail="Request timed out"
#         )
#     except Exception as e:
#         await db.rollback()
#         logging.error(f"Error processing webhook: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal server error: {str(e)}"
#         )
        





# @router.post("/site-data/webhook")
# async def webhook_handler(request: Request):
#     data = await request.json()
#     print("Webhook received:", data)  # This will print the webhook data
#     return {"status": "success", "message": "Webhook received"}




     
# @router.post("/webhook/users")
# async def user_webhook(data: dict):
#     try:
#         logger.info(f"Received request at /webhook/users with data: {data}")
#         print("Received user webhook data:", data)
#         return {"status": "received"}
#     except Exception as e:
#         logger.error(f"Error processing webhook: {str(e)}")
#         # It's good practice to include the stack trace in error logs
#         logger.exception("Full error details:")
#         raise

# @router.post("/webhook/modules", tags=["dashboard"])
# async def module_webhook(data: dict):
#     try:
#         logger.info(f"Received module webhook data: {data}")
#         return {"status": "received"}
#     except Exception as e:
#         logger.error(f"Error processing module webhook: {str(e)}")
#         logger.exception("Full error details:")
#         raise

# @router.post("/webhook/sites", tags=["dashboard"])
# async def site_webhook(data: dict):
#     try:
#         logger.info(f"Received site webhook data: {data}")
#         return {"status": "received"}
#     except Exception as e:
#         logger.error(f"Error processing site webhook: {str(e)}")
#         logger.exception("Full error details:")
#         raise



# @router.post("/webhook/site-data")
# async def receive_site_data(request: Request, db: AsyncSession = Depends(get_db)):
#     """
#     Receives consolidated site data from the webhook, updates or creates corresponding
#     SiteData records for the associated user, commits changes, and refreshes the objects.
#     """
#     try:
#         # Parse JSON payload
#         data = await request.json()
#         logger.info(f"Received webhook: {data}")

#         # Check for success status in payload
#         if data.get("status") != "success":
#             error_msg = data.get("message", "Unknown error")
#             logger.error(f"Error in webhook data: {error_msg}")
#             return {"status": "error", "message": f"Received error data: {error_msg}"}

#         # Extract email from first site's site_info
#         sites_data = data.get("data", {}).get("sites_data", [])
#         email = None
#         if sites_data and "site_info" in sites_data[0]:
#             email = sites_data[0]["site_info"].get("email")
#         if not email:
#             logger.error("Email not found in webhook data")
#             return {"status": "error", "message": "Email not found in data"}

#         # Fetch user from database using the email
#         result = await db.execute(select(User).filter(User.email == email))
#         user = result.scalar_one_or_none()
#         if not user:
#             logger.warning(f"No user found for email: {email}")
#             return {"status": "error", "message": f"No user found for email: {email}"}

#         # Process each site data entry
#         totals = data.get("data", {}).get("totals", {})
#         total_sites_count = totals.get("total_sites", 0)
#         active_sites_count = totals.get("active_sites", 0)

#         updated_sites = 0

#         for site in sites_data:
#             site_info = site.get("site_info", {})
#             stats = site.get("stats", {})
#             site_name = site_info.get("site_name")
#             site_status = site_info.get("site_status")
#             country = site_info.get("country")

#             if not site_name:
#                 logger.error("Site name missing in site data")
#                 continue

#             # Check if the site already exists in the database
#             result = await db.execute(select(SiteData).filter(SiteData.site_name == site_name))
#             existing_site = result.scalar_one_or_none()

#             if existing_site:
#                 # Update the existing site's stats and info
#                 existing_site.total_users_count = stats.get("total_users", 0)
#                 existing_site.active_users_count = stats.get("active_users", 0)
#                 existing_site.active_modules_count = stats.get("active_modules", 0)
#                 existing_site.active_sites = site_status
#                 existing_site.location = country 
#                 existing_site.total_users = stats.get("users", [])
#                 existing_site.active_users = stats.get("active_users_list", [])
#                 existing_site.active_modules = stats.get("modules", [])
#                 existing_site.sites_data = site  # Store full site data
#                 existing_site.updated_at = datetime.now()
#                 existing_site.total_site_counts = total_sites_count  # Update total_site_counts
#                 existing_site.active_site_counts = active_sites_count  # Update active_site_counts
#                 logger.info(f"Updated site: {site_name}")
#             else:
#                 # Create a new SiteData record
#                 new_site = SiteData(
#                     site_name=site_name,
#                     active_sites=site_status,
#                     location=country,
#                     total_users_count=stats.get("total_users", 0),
#                     active_users_count=stats.get("active_users", 0),
#                     active_modules_count=stats.get("active_modules", 0),
#                     total_users=stats.get("users", []),
#                     active_users=stats.get("active_users_list", []),
#                     active_modules=stats.get("modules", []),
#                     sites_data=site,
#                     user_id=user.id,
#                     total_site_counts=total_sites_count,  # Set total_site_counts
#                     active_site_counts=active_sites_count  # Set active_site_counts
#                 )
#                 db.add(new_site)
#                 logger.info(f"Created new site: {site_name}")

#             updated_sites += 1

#         # Commit the database changes
#         await db.commit()

#         # Refresh each site record to ensure latest state is loaded
#         for site in sites_data:
#             site_name = site.get("site_info", {}).get("site_name")
#             if site_name:
#                 result = await db.execute(select(SiteData).filter(SiteData.site_name == site_name))
#                 refreshed_site = result.scalar_one_or_none()
#                 if refreshed_site:
#                     await db.refresh(refreshed_site)

#         # Log summary information
#         logger.info(f"Site Data Summary - Email: {email}, Updated Sites: {updated_sites}, "
#                     f"Total Sites (from payload): {total_sites_count}, "
#                     f"Active Sites (from payload): {active_sites_count}")

#         return {
#             "status": "success",
#             "message": f"Updated {updated_sites} sites for user {email}",
#             "updated_sites": updated_sites
#         }

#     except Exception as e:
#         logger.exception("An error occurred while processing the webhook data")
#         return {"status": "error", "message": str(e)}  
    










# @router.post("/webhook/site-data")
# async def receive_site_data(request: Request, db: AsyncSession = Depends(get_db)):
#     """
#     Receives consolidated site data from the webhook, updates or creates corresponding
#     SiteData records for the associated user, commits changes, and refreshes the objects.
#     """
#     try:
#         # Parse JSON payload
#         data = await request.json()
#         logger.info(f"Received webhook: {data}")

#         # Check for success status in payload
#         if data.get("status") != "success":
#             error_msg = data.get("message", "Unknown error")
#             logger.error(f"Error in webhook data: {error_msg}")
#             return {"status": "error", "message": f"Received error data: {error_msg}"}

#         # Extract email from first site's site_info
#         sites_data = data.get("data", {}).get("sites_data", [])
#         email = None
#         if sites_data and "site_info" in sites_data[0]:
#             email = sites_data[0]["site_info"].get("email")
#         if not email:
#             logger.error("Email not found in webhook data")
#             return {"status": "error", "message": "Email not found in data"}

#         # Fetch user from database using the email
#         result = await db.execute(select(User).filter(User.email == email))
#         user = result.scalar_one_or_none()
#         if not user:
#             logger.warning(f"No user found for email: {email}")
#             return {"status": "error", "message": f"No user found for email: {email}"}

#         # Process each site data entry
#         totals = data.get("data", {}).get("totals", {})
#         print("OKPATUKPTUKPO33333333333333333333344434343434333333333333333FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", totals)
        
#         # total_sites_count = totals.get("total_sites", 0)
#         # active_sites_count = totals.get("active_sites", 0)
        
#         updated_sites = 0

#         for site in sites_data:
#             site_info = site.get("site_info", {})
#             stats = site.get("stats", {})
#             site_name = site_info.get("site_name")
#             site_status = site_info.get("site_status")
#             country = site_info.get("country")

#             if not site_name:
#                 logger.error("Site name missing in site data")
#                 continue

#             # Check if the site already exists in the database
#             result = await db.execute(select(SiteData).filter(SiteData.site_name == site_name))
#             existing_site = result.scalar_one_or_none()

#             if existing_site:
#                 # Update the existing site's stats and info
#                 existing_site.total_users_count = stats.get("total_users", 0)
#                 existing_site.active_users_count = stats.get("active_users", 0)
#                 existing_site.active_modules_count = stats.get("active_modules", 0)
#                 existing_site.active_sites = site_status
#                 existing_site.location = country 
#                 existing_site.total_users = stats.get("users", [])
#                 existing_site.active_users = stats.get("active_users_list", [])
#                 existing_site.active_modules = stats.get("modules", [])
#                 existing_site.sites_data = site  # Store full site data
#                 existing_site.updated_at = datetime.now()
#                 existing_site.total_site_counts = totals.get("total_sites", 0)
#                 existing_site.active_site_counts = totals.get("active_sites", 0)
#                 existing_site.updated_at = datetime.now()
                
#                 logger.info(f"Updated site: {site_name}")
#             else:
#                 # Create a new SiteData record
#                 new_site = SiteData(
#                     site_name=site_name,
#                     active_sites=site_status,
#                     location=country,
#                     total_users_count=stats.get("total_users", 0),
#                     active_users_count=stats.get("active_users", 0),
#                     active_modules_count=stats.get("active_modules", 0),
#                     total_users=stats.get("users", []),
#                     active_users=stats.get("active_users_list", []),
#                     active_modules=stats.get("modules", []),
#                     sites_data=site,
#                     user_id=user.id
#                 )
#                 db.add(new_site)
#                 logger.info(f"Created new site: {site_name}")

#             updated_sites += 1

#         # Commit the database changes
#         await db.commit()

#         # Refresh each site record to ensure latest state is loaded
#         for site in sites_data:
#             site_name = site.get("site_info", {}).get("site_name")
#             if site_name:
#                 result = await db.execute(select(SiteData).filter(SiteData.site_name == site_name))
#                 refreshed_site = result.scalar_one_or_none()
#                 if refreshed_site:
#                     await db.refresh(refreshed_site)

#         # Log summary information
#         logger.info(f"Site Data Summary - Email: {email}, Updated Sites: {updated_sites}, "
#                     f"Total Sites (from payload): {totals.get('total_sites', 0)}, "
#                     f"Active Sites (from payload): {totals.get('active_sites', 0)}")

#         return {
#             "status": "success",
#             "message": f"Updated {updated_sites} sites for user {email}",
#             "updated_sites": updated_sites
#         }

#     except Exception as e:
#         logger.exception("An error occurred while processing the webhook data")
#         return {"status": "error", "message": str(e)}

# @router.get("/sites-data", tags=["dashboard"])
# async def fetch_site_data(id: str, db: AsyncSession = Depends(get_db)):
#     """
#     Fetch site data for the given user ID.
#     """
#     if not id:
#         raise HTTPException(status_code=400, detail="Query parameter 'id' is required")

#     try:
#         data = await get_site_data(id=id, db=db)
#         return data
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")