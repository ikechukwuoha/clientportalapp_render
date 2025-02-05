import os
from sqlalchemy.future import select
import httpx
import logging
import traceback
from fastapi import Depends, HTTPException


from datetime import datetime, timedelta
import logging
import httpx
from sqlalchemy import select
from app.api.models.site_data import SiteData
from app.api.models.user_model import User
from app.api.database.db import get_db 
from sqlalchemy.ext.asyncio import AsyncSession


from typing import Optional


# API_KEY = os.getenv("API_KEY")
# API_SECRET = os.getenv("API_SECRET")
# API_KEY = "7a6c5c848566ccb"
# API_SECRET = "7841288d219f16c"
# API_URL = "http://localhost:8000/api/method/clientportalapp_admin.users.get_users"


async def fetch_total_users():
    headers = {
        # "Authorization": f"token {API_KEY}:{API_SECRET}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://clientportal.org:8080/api/method/clientportalapp_admin.users.get_users")
            response.raise_for_status()
            data = response.json()

            user_data = data.get("message", {})
            if not user_data:
                logging.warning("No users found in the response.")
                return {"count": 0, "users": []}

            return {
                "count": user_data.get("count", 0),
                "users": user_data.get("users", [])
            }

    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        raise

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    
    
    

async def fetch_active_users():
    headers = {
        # "Authorization": f"token {API_KEY}:{API_SECRET}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://clientportal.org:8080/api/method/clientportalapp_admin.users.get_active_users") #pass the URl Dynamically
            response.raise_for_status()
            data = response.json()

            user_data = data.get("message", {})
            if not user_data:
                logging.warning("No users found in the response.")
                return {"count": 0, "users": []}

            return {
                "count": user_data.get("count", 0),
                "users": user_data.get("users", [])
            }

    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        raise

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    
    
    
    
    

async def fetch_active_modules():
    headers = {
        # "Authorization": f"token {API_KEY}:{API_SECRET}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://clientportal.org:8080/api/method/clientportalapp_admin.modules.get_modules")
            response.raise_for_status()
            data = response.json()

            module_data = data.get("message", {})
            if not module_data:
                logging.warning("No modules found in the response.")
                return {"count": 0, "modules": []}

            return {
                "count": module_data.get("count", 0),
                "modules": module_data.get("modules", [])
            }

    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        raise

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    
    
    
    
    
    

async def fetch_active_sites(email: str):
    headers = {
        # "Authorization": f"token {API_KEY}:{API_SECRET}"
    }

    try:
        params = {"email": email}  # Add email to query parameters

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://clientportal.org:8080/api/method/clientportalapp_admin.sites.get_sites",
                params=params  # Pass the email parameter here
            )
            response.raise_for_status()
            data = response.json()

            module_data = data.get("message", {})
            if not module_data:
                logging.warning("No sites found in the response.")
                return {"count": 0, "site": []}

            return {
                "count": len(module_data),  # Get the count from the data length
                "sites": module_data  # Directly return the list of sites
            }

    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        raise

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    
    
    
    
    
    
    

async def fetch_active_users_dynamic(email: str):
    # Step 1: Fetch the active sites
    active_sites_response = await fetch_active_sites(email=email)
    print("ACTIVE SITE RESPoNSE111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111", active_sites_response)

    if active_sites_response["count"] == 0:
        logging.warning("No sites found for the given email.")
        return {"count": 0, "users": []}

    # Step 2: Extract the `message` list from the `sites` dictionary
    sites = active_sites_response["sites"].get("sites", {}).get("message", [])
    if not sites:
        logging.warning("No sites found in the `message` key.")
        return {"count": 0, "users": []}

    # Step 3: Extract the first site_name (assuming one site for simplicity)
    site_name = sites[0]["site_name"]

    # Step 4: Dynamically use `site_name` in the second API call URL
    # can I call the fetch_total_users, fetch_active_users, fetch_active_modules and display the active sites of this email
    headers = {
        # "Authorization": f"token {API_KEY}:{API_SECRET}"
    }
    url = f"http://{site_name}/api/method/clientportalapp_admin.users.get_active_users"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            user_data = data.get("message", [])
            if not user_data:
                logging.warning("No users found in the response.")
                return {"count": 0, "users": []}

            return {
                "count": len(user_data),  # Get the count from the data length
                "users": user_data  # Directly return the list of users
            }

    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        raise

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    



async def fetch_user_data(email: str, db: AsyncSession):
    # Step 1: Fetch active sites
    active_sites_response = await fetch_active_sites(email=email)

    if active_sites_response["count"] == 0:
        logging.warning("No sites found for the given email.")
        return {
            "sites_data": [],
            "totals": {
                "total_sites": 0,
                "total_users": 0,
                "active_users": 0,
                "active_modules": 0,
            }
        }

    sites = active_sites_response["sites"].get("sites", {}).get("message", [])
    if not sites:
        logging.warning("No sites found in the `message` key.")
        return {
            "sites_data": [],
            "totals": {
                "total_sites": 0,
                "total_users": 0,
                "active_users": 0,
                "active_modules": 0,
            }
        }

    # Initialize aggregated totals
    total_users_count = 0
    active_users_count = 0
    active_modules_count = 0

    sites_data = []
    
    # Fetch user from database once, outside the loop
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    async with httpx.AsyncClient() as client:
        for site in sites:
            site_name = site.get("site_name")
            if not site_name:
                continue

            urls = {
                "total_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_users",
                "active_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_active_users",
                "active_modules": f"http://{site_name}/api/method/clientportalapp_admin.modules.get_modules",
            }

            try:
                # Fetch data for current site
                total_users_response = await client.get(urls["total_users"])
                total_users_response.raise_for_status()

                active_users_response = await client.get(urls["active_users"])
                active_users_response.raise_for_status()

                active_modules_response = await client.get(urls["active_modules"])
                active_modules_response.raise_for_status()

                # Parse responses for current site
                total_users_data = total_users_response.json().get("message", {})
                active_users_data = active_users_response.json().get("message", {})
                active_modules_data = active_modules_response.json().get("message", {})
                
                # Get counts for current site
                site_total_users = total_users_data.get("count", 0)
                site_active_users = active_users_data.get("count", 0)
                site_active_modules = active_modules_data.get("count", 0)

                # Update global totals
                total_users_count += site_total_users
                active_users_count += site_active_users
                active_modules_count += site_active_modules

                # Add or update site-specific data in the database
                existing_site = await db.execute(
                    select(SiteData).filter(SiteData.site_name == site_name)
                )
                existing_site = existing_site.scalars().first()

                if existing_site:
                    # Update existing site with its specific counts
                    existing_site.total_users_count = site_total_users  # Use site-specific count
                    existing_site.active_users_count = site_active_users  # Use site-specific count
                    existing_site.active_sites = site.get('active', False)
                    existing_site.location = site.get('country', None)
                    existing_site.active_modules_count = site_active_modules  # Use site-specific count
                    existing_site.total_users = total_users_data.get("users", [])
                    existing_site.active_users = active_users_data.get("users", [])
                    existing_site.active_modules = active_modules_data.get("modules", [])
                    existing_site.sites_data = {
                        "total_users": total_users_data,
                        "active_users": active_users_data,
                        "active_modules": active_modules_data
                    }
                else:
                    # Create new site with its specific counts
                    site_data = SiteData(
                        site_name=site_name,
                        total_users_count=site_total_users,  # Use site-specific count
                        active_users_count=site_active_users,  # Use site-specific count
                        active_sites=site.get('active', False),
                        location=site.get('country', None),
                        active_modules_count=site_active_modules,  # Use site-specific count
                        total_users=total_users_data.get("users", []),
                        active_users=active_users_data.get("users", []),
                        active_modules=active_modules_data.get("modules", []),
                        sites_data={
                            "total_users": total_users_data,
                            "active_users": active_users_data,
                            "active_modules": active_modules_data
                        },
                        user_id=user.id if user else None
                    )
                    db.add(site_data)

                # Add site-specific data to the response
                sites_data.append({
                    "site_data": site,
                    "total_users": {
                        "count": site_total_users,
                        "users": total_users_data.get("users", [])
                    },
                    "active_users": {
                        "count": site_active_users,
                        "users": active_users_data.get("users", [])
                    },
                    "active_modules": {
                        "count": site_active_modules,
                        "modules": active_modules_data.get("modules", [])
                    }
                })

            except httpx.RequestError as e:
                logging.error(f"Request error on site {site_name}: {e}")
            except httpx.HTTPStatusError as e:
                logging.error(f"HTTP error on site {site_name}: {e.response.status_code} - {e.response.text}")

        # Commit changes to the database
        await db.commit()

        active_sites_count = active_sites_response["sites"]['totals']['active_sites']

        return {
            "totals": {
                "total_sites": len(sites),
                "active_sites": active_sites_count,
                "total_users": total_users_count,
                "active_users": active_users_count,
                "total_active_modules": active_modules_count,
            },
            "sites_data": sites_data,
        }


async def fetch_user_data_count(email: str):
    # Step 1: Fetch active sites
    active_sites_response = await fetch_active_sites(email=email)

    if active_sites_response["count"] == 0:
        logging.warning("No sites found for the given email.")
        return {
            "active_sites": {"count": 0, "sites": []},
            "total_users": {"count": 0, "users": []},
            "active_users": {"count": 0, "users": []},
            "active_modules": {"count": 0, "modules": []},
        }

    # Extract all sites dynamically
    sites = active_sites_response["sites"].get("sites", {}).get("message", [])
    if not sites:
        logging.warning("No sites found in the `message` key.")
        return {
            "active_sites": {"count": 0, "sites": []},
            "total_users": {"count": 0, "users": []},
            "active_users": {"count": 0, "users": []},
            "active_modules": {"count": 0, "modules": []},
        }

    # Initialize global counters and result aggregators
    total_users_count = 0
    total_users_list = []
    active_users_count = 0
    active_users_list = []
    active_modules_count = 0
    active_modules_list = []

    headers = {
        # "Authorization": f"token {API_KEY}:{API_SECRET}"
    }

    # Step 2: Loop through all sites and fetch data
    async with httpx.AsyncClient() as client:
        for site in sites:
            site_name = site.get("site_name")
            if not site_name:
                continue

            # Define dynamic URLs
            urls = {
                "total_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_users",
                "active_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_active_users",
                "active_modules": f"http://{site_name}/api/method/clientportalapp_admin.modules.get_modules"
            }

            try:
                # Fetch data from each site
                total_users_response = await client.get(urls["total_users"])
                total_users_response.raise_for_status()

                active_users_response = await client.get(urls["active_users"])
                active_users_response.raise_for_status()

                active_modules_response = await client.get(urls["active_modules"])
                active_modules_response.raise_for_status()

                # Parse responses
                total_users_data = total_users_response.json().get("message", {})
                active_users_data = active_users_response.json().get("message", {})
                active_modules_data = active_modules_response.json().get("message", {})

                # Aggregate global data
                total_users_count += total_users_data.get("count", 0)
                total_users_list.extend(total_users_data.get("users", []))

                active_users_count += active_users_data.get("count", 0)
                active_users_list.extend(active_users_data.get("users", []))

                active_modules_count += active_modules_data.get("count", 0)
                active_modules_list.extend(active_modules_data.get("modules", []))

                # Add site-specific data
                site["total_users"] = {
                    "count": total_users_data.get("count", 0),
                    f"total_users_for_{site_name}": total_users_data.get("users", [])
                }
                site["active_users"] = {
                    "count": active_users_data.get("count", 0),
                    f"active_users_for_{site_name}": active_users_data.get("users", [])
                }
                site["active_modules"] = {
                    "count": active_modules_data.get("count", 0),
                    f"active_modules_for_{site_name}": active_modules_data.get("modules", [])
                }

            except httpx.RequestError as e:
                logging.error(f"Request error on site {site_name}: {e}")
            except httpx.HTTPStatusError as e:
                logging.error(f"HTTP error on site {site_name}: {e.response.status_code} - {e.response.text}")

    # Step 3: Return consolidated data
    return {
        "active_sites": {
            "count": len(sites),
            "sites": sites
        },
        "total_users": {
            "count": total_users_count,
            "users": total_users_list
        },
        "active_users": {
            "count": active_users_count,
            "users": active_users_list
        },
        "active_modules": {
            "count": active_modules_count,
            "modules": active_modules_list
        },
    }


async def get_site_data(id: str, db: AsyncSession):
    """
    Fetch and update site data with real-time checks.
    
    Prioritizes database lookup, then performs real-time checks for updates.
    """
    # First, attempt to retrieve existing site data from database
    result = await db.execute(select(SiteData).where(SiteData.user_id == id))
    user_sites = result.scalars().all()

    # If sites exist in database, check for real-time updates
    if user_sites:
        async with httpx.AsyncClient() as client:
            updated_sites_data = []
            total_users_count = 0
            active_users_count = 0
            active_modules_count = 0
            active_sites_count = 0

            for site in user_sites:
                try:
                    # Real-time API calls to check for updates
                    urls = {
                        "total_users": f"http://{site.site_name}/api/method/clientportalapp_admin.users.get_users",
                        "active_users": f"http://{site.site_name}/api/method/clientportalapp_admin.users.get_active_users",
                        "active_modules": f"http://{site.site_name}/api/method/clientportalapp_admin.modules.get_modules",
                    }

                    # Parallel API calls for efficiency
                    total_users_response = await client.get(urls["total_users"])
                    active_users_response = await client.get(urls["active_users"])
                    active_modules_response = await client.get(urls["active_modules"])

                    total_users_data = total_users_response.json().get("message", {})
                    active_users_data = active_users_response.json().get("message", {})
                    active_modules_data = active_modules_response.json().get("message", {})

                    # Extract current counts
                    site_total_users = total_users_data.get("count", 0)
                    site_active_users = active_users_data.get("count", 0)
                    site_active_modules = active_modules_data.get("count", 0)

                    # Update database record
                    site.total_users_count = site_total_users
                    site.active_users_count = site_active_users
                    site.active_modules_count = site_active_modules
                    site.total_users = total_users_data.get("users", [])
                    site.active_users = active_users_data.get("users", [])
                    site.active_modules = active_modules_data.get("modules", [])

                    # Aggregate totals
                    total_users_count += site_total_users
                    active_users_count += site_active_users
                    active_modules_count += site_active_modules
                    active_sites_count += 1 if site.active_sites else 0

                    # Prepare site data for response
                    updated_sites_data.append({
                        "site_name": site.site_name,
                        "active": site.active_sites,
                        "creation_date": site.created_at,
                        "country": site.location,
                        "total_users": {
                            "count": site_total_users,
                            "users": total_users_data.get("users", []),
                        },
                        "active_users": {
                            "count": site_active_users,
                            "users": active_users_data.get("users", []),
                        },
                        "active_modules": {
                            "count": site_active_modules,
                            "modules": active_modules_data.get("modules", []),
                        },
                    })

                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logging.error(f"Update error for site {site.site_name}: {e}")
                    # Use existing data if update fails
                    updated_sites_data.append({
                        "site_name": site.site_name,
                        "active": site.active_sites,
                        "creation_date": site.created_at,
                        "country": site.location,
                        "total_users": {
                            "count": site.total_users_count,
                            "users": site.total_users,
                        },
                        "active_users": {
                            "count": site.active_users_count,
                            "users": site.active_users,
                        },
                        "active_modules": {
                            "count": site.active_modules_count,
                            "modules": site.active_modules,
                        },
                    })

            # Commit updates to database
            await db.commit()

            return {
                "totals": {
                    "total_sites": len(user_sites),
                    "active_sites": active_sites_count,
                    "total_users": total_users_count,
                    "active_users": active_users_count,
                    "total_active_modules": active_modules_count,
                },
                "sites_data": updated_sites_data,
            }

    # Fallback to original fetch_user_data if no existing sites
    return await fetch_user_data(id=id, db=db)




# async def get_site_data(id: str, db: AsyncSession):
#     """
#     Fetch site data from the database for the given user ID.
#     """
#     # Query the database for site data matching the user's ID
#     result = await db.execute(select(SiteData).where(SiteData.user_id == id))
#     user_sites = result.scalars().all()

#     # If data exists, process and return it
#     if user_sites:
#         return {
#             "totals": {
#                 "total_sites": len(user_sites),
#                 "active_sites": sum(1 for site in user_sites if site.active_sites),
#                 "total_users": sum(site.total_users_count for site in user_sites),
#                 "active_users": sum(site.active_users_count for site in user_sites),
#                 "total_active_modules": sum(site.active_modules_count for site in user_sites),
#             },
#             "sites_data": [
#                 {
#                     "site_name": site.site_name,
#                     "active": site.active_sites,
#                     "creation_date":site.created_at,
#                     "country":site.location,
#                     "total_users": {
#                         "count": site.total_users_count,
#                         "users": site.total_users,
#                     },
#                     "active_users": {
#                         "count": site.active_users_count,
#                         "users": site.active_users,
#                     },
#                     "active_modules": {
#                         "count": site.active_modules_count,
#                         "modules": site.active_modules,
#                     },
#                 }
#                 for site in user_sites
#             ],
#         }

#     # If no data exists, fetch it using `fetch_user_data`
#     return await fetch_user_data(id=id, db=db)





# async def fetch_user_data(email: str, db: AsyncSession):
#     # Step 1: Fetch active sites
#     active_sites_response = await fetch_active_sites(email=email)

#     if active_sites_response["count"] == 0:
#         logging.warning("No sites found for the given email.")
#         return {
#             "sites_data": [],
#             "totals": {
#                 "total_sites": 0,
#                 "total_users": 0,
#                 "active_users": 0,
#                 "active_modules": 0,
#             }
#         }

#     # Extract all sites dynamically
#     sites = active_sites_response["sites"].get("sites", {}).get("message", [])
#     if not sites:
#         logging.warning("No sites found in the `message` key.")
#         return {
#             "sites_data": [],
#             "totals": {
#                 "total_sites": 0,
#                 "total_users": 0,
#                 "active_users": 0,
#                 "active_modules": 0,
#             }
#         }

#     # Initialize aggregated totals
#     total_users_count = 0
#     active_users_count = 0
#     active_modules_count = 0

#     # List to hold site-specific data
#     sites_data = []

#     headers = {
#         # "Authorization": f"token {API_KEY}:{API_SECRET}"
#     }

#     # Step 2: Loop through all sites and fetch data
#     async with httpx.AsyncClient() as client:
#         for site in sites:
#             site_name = site.get("site_name")
#             if not site_name:
#                 continue

#             # Define dynamic URLs
#             urls = {
#                 "total_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_users",
#                 "active_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_active_users",
#                 "active_modules": f"http://{site_name}/api/method/clientportalapp_admin.modules.get_modules",
#             }

#             try:
#                 # Fetch data from each site
#                 total_users_response = await client.get(urls["total_users"])
#                 total_users_response.raise_for_status()

#                 active_users_response = await client.get(urls["active_users"])
#                 active_users_response.raise_for_status()

#                 active_modules_response = await client.get(urls["active_modules"])
#                 active_modules_response.raise_for_status()

#                 # Parse responses
#                 total_users_data = total_users_response.json().get("message", {})
#                 active_users_data = active_users_response.json().get("message", {})
#                 active_modules_data = active_modules_response.json().get("message", {})
#                 active_sites_data = active_sites_response["sites"]
                
#                 print("Active Sites Data2222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222", active_sites_data)
                

#                 # Update totals
#                 total_users_count += total_users_data.get("count", 0)
#                 active_users_count += active_users_data.get("count", 0)
#                 active_modules_count += active_modules_data.get("count", 0)
#                 active_sites_count = active_sites_data['totals']['active_sites']
#                 # Fetch the active sites from the response
#                 actives_sites = active_sites_data['sites'].get('message', [])

#                 # Extract active statuses from all sites
#                 active_sites_active = [site.get('active', False) for site in actives_sites]
                
#                 print("ACTIVE SITE COUNT9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999", active_sites_active)
                
#                 result = await db.execute(select(User).filter(User.email == email))
#                 user = result.scalar_one_or_none() 
                
               

#                 # Add site-specific data to the list
#                 existing_site = await db.execute(select(SiteData).filter(SiteData.site_name == site_name))
#                 existing_site = existing_site.scalars().first()

#                 if existing_site:
#                     # Update existing site
#                     existing_site.total_users_count = total_users_count
#                     existing_site.active_users_count = active_users_count
#                     existing_site.active_sites = site.get('active', False)
#                     existing_site.active_modules_count = active_modules_count
#                     existing_site.total_users = total_users_data.get("users", [])
#                     existing_site.active_users = active_users_data.get("users", [])
#                     existing_site.active_modules = active_modules_data.get("modules", [])
#                     existing_site.sites_data = {
#                         "total_users": total_users_data,
#                         "active_users": active_users_data,
#                         "active_modules": active_modules_data
#                     }
#                 else:
#                     # Create new site
#                     site_data = SiteData(
#                         site_name=site_name,
#                         total_users_count=total_users_count,
#                         active_users_count=active_users_count,
#                         active_sites=site.get('active', False),
#                         active_modules_count=active_modules_count,
#                         total_users=total_users_data.get("users", []),
#                         active_users=active_users_data.get("users", []),
#                         active_modules=active_modules_data.get("modules", []),
#                         sites_data={
#                             "total_users": total_users_data,
#                             "active_users": active_users_data,
#                             "active_modules": active_modules_data
#                         },
#                         user_id=user.id
#                     )
#                     db.add(site_data)

#                 # Add site-specific data, including the full site response
#                 sites_data.append({
#                     #"site_name": site_name,
#                     "site_data": site,
#                     "total_users": {
#                         "count": total_users_data.get("count", 0),
#                         "users": total_users_data.get("users", [])
#                     },
#                     "active_users": {
#                         "count": active_users_data.get("count", 0),
#                         "users": active_users_data.get("users", [])
#                     },
#                     # "site_data": {  # This is where we add the full site data response
#                     #     "total_users": total_users_data,
#                     #     "active_users": active_users_data,
#                     #     "active_modules": active_modules_data
#                     # },
#                     "active_modules": {
#                         "count": active_modules_data.get("count", 0),
#                         "modules": active_modules_data.get("modules", [])
#                     }
#                 })

#             except httpx.RequestError as e:
#                 logging.error(f"Request error on site {site_name}: {e}")
#             except httpx.HTTPStatusError as e:
#                 logging.error(f"HTTP error on site {site_name}: {e.response.status_code} - {e.response.text}")

#     # Commit the changes to the DB
#     await db.commit()

#     # Step 3: Return consolidated data
#     return {
#         "totals": {
#             "total_sites": len(sites),
#             "active_sites": active_sites_count,
#             "total_users": total_users_count,
#             "active_users": active_users_count,
#             "total_active_modules": active_modules_count,
#         },
#         "sites_data": sites_data,
#     }



# async def fetch_user_data_count(email: str):
#     # Step 1: Fetch active sites
#     active_sites_response = await fetch_active_sites(email=email)

#     if active_sites_response["count"] == 0:
#         logging.warning("No sites found for the given email.")
#         return {
#             "active_sites": {"count": 0, "sites": []},
#             "total_users": {"count": 0, "users": []},
#             "active_users": {"count": 0, "users": []},
#             "active_modules": {"count": 0, "modules": []},
#         }

#     # Extract all sites dynamically
#     sites = active_sites_response["sites"].get("sites", {}).get("message", [])
#     if not sites:
#         logging.warning("No sites found in the `message` key.")
#         return {
#             "active_sites": {"count": 0, "sites": []},
#             "total_users": {"count": 0, "users": []},
#             "active_users": {"count": 0, "users": []},
#             "active_modules": {"count": 0, "modules": []},
#         }

#     # Initialize counters and result aggregators
#     total_users_count = 0
#     total_users_list = []
#     active_users_count = 0
#     active_users_list = []
#     active_modules_count = 0
#     active_modules_list = []

#     headers = {
#         # "Authorization": f"token {API_KEY}:{API_SECRET}"
#     }

#     # Step 2: Loop through all sites and fetch data
#     async with httpx.AsyncClient() as client:
#         for site in sites:
#             site_name = site.get("site_name")
#             if not site_name:
#                 continue

#             # Define dynamic URLs
#             urls = {
#                 "total_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_users",
#                 "active_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_active_users",
#                 "active_modules": f"http://{site_name}/api/method/clientportalapp_admin.modules.get_modules"
#             }

#             try:
#                 # Fetch data from each site
#                 total_users_response = await client.get(urls["total_users"])
#                 total_users_response.raise_for_status()

#                 active_users_response = await client.get(urls["active_users"])
#                 active_users_response.raise_for_status()

#                 active_modules_response = await client.get(urls["active_modules"])
#                 active_modules_response.raise_for_status()

#                 # Parse responses
#                 total_users_data = total_users_response.json().get("message", {})
#                 active_users_data = active_users_response.json().get("message", {})
#                 active_modules_data = active_modules_response.json().get("message", {})

#                 # Aggregate data
#                 total_users_count += total_users_data.get("count", 0)
#                 total_users_list.extend(total_users_data.get("users", []))

#                 active_users_count += active_users_data.get("count", 0)
#                 active_users_list.extend(active_users_data.get("users", []))

#                 active_modules_count += active_modules_data.get("count", 0)
#                 active_modules_list.extend(active_modules_data.get("modules", []))

#             except httpx.RequestError as e:
#                 logging.error(f"Request error on site {site_name}: {e}")
#             except httpx.HTTPStatusError as e:
#                 logging.error(f"HTTP error on site {site_name}: {e.response.status_code} - {e.response.text}")

#     # Step 3: Return consolidated data
#     return {
#         "active_sites": {
#             "count": len(sites),
#             "sites": sites
#         },
#         "total_users": {
#             "count": total_users_count,
#             "users": total_users_list
#         },
#         "active_users": {
#             "count": active_users_count,
#             "users": active_users_list
#         },
#         "active_modules": {
#             "count": active_modules_count,
#             "modules": active_modules_list
#         },
#     }




# async def fetch_user_data(email: str, db: AsyncSession):
#     # Step 1: Fetch active sites
#     active_sites_response = await fetch_active_sites(email=email)

#     if active_sites_response["count"] == 0:
#         logging.warning("No sites found for the given email.")
#         return {
#             "sites_data": [],
#             "totals": {
#                 "total_sites": 0,
#                 "total_users": 0,
#                 "active_users": 0,
#                 "active_modules": 0,
#             }
#         }

#     # Extract all sites dynamically
#     sites = active_sites_response["sites"].get("sites", {}).get("message", [])
#     if not sites:
#         logging.warning("No sites found in the `message` key.")
#         return {
#             "sites_data": [],
#             "totals": {
#                 "total_sites": 0,
#                 "total_users": 0,
#                 "active_users": 0,
#                 "active_modules": 0,
#             }
#         }

#     # Initialize aggregated totals
#     total_users_count = 0
#     active_users_count = 0
#     active_modules_count = 0

#     # List to hold site-specific data
#     sites_data = []

#     headers = {
#         # "Authorization": f"token {API_KEY}:{API_SECRET}"
#     }

#     # Step 2: Loop through all sites and fetch data
#     async with httpx.AsyncClient() as client:
#         for site in sites:
#             site_name = site.get("site_name")
#             if not site_name:
#                 continue

#             # Define dynamic URLs
#             urls = {
#                 "total_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_users",
#                 "active_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_active_users",
#                 "active_modules": f"http://{site_name}/api/method/clientportalapp_admin.modules.get_modules"
#             }

#             try:
#                 # Fetch data from each site
#                 total_users_response = await client.get(urls["total_users"])
#                 total_users_response.raise_for_status()

#                 active_users_response = await client.get(urls["active_users"])
#                 active_users_response.raise_for_status()

#                 active_modules_response = await client.get(urls["active_modules"])
#                 active_modules_response.raise_for_status()

#                 # Parse responses
#                 total_users_data = total_users_response.json().get("message", {})
#                 active_users_data = active_users_response.json().get("message", {})
#                 active_modules_data = active_modules_response.json().get("message", {})

#                 # Update totals
#                 total_users_count += total_users_data.get("count", 0)
#                 active_users_count += active_users_data.get("count", 0)
#                 active_modules_count += active_modules_data.get("count", 0)

#                 # Add site-specific data to the list
#                 sites_data.append({
#                     "site_name": site_name,
#                     "total_users": {
#                         "count": total_users_data.get("count", 0),
#                         "users": total_users_data.get("users", [])
#                     },
#                     "active_users": {
#                         "count": active_users_data.get("count", 0),
#                         "users": active_users_data.get("users", [])
#                     },
#                     "active_modules": {
#                         "count": active_modules_data.get("count", 0),
#                         "modules": active_modules_data.get("modules", [])
#                     }
#                 })

#             except httpx.RequestError as e:
#                 logging.error(f"Request error on site {site_name}: {e}")
#             except httpx.HTTPStatusError as e:
#                 logging.error(f"HTTP error on site {site_name}: {e.response.status_code} - {e.response.text}")

#     # Step 3: Return consolidated data
#     return {
#         "totals": {
#             "active_sites": len(sites),
#             "total_users": total_users_count,
#             "active_users": active_users_count,
#             "total_active_modules": active_modules_count,
#         },
#         "sites_data": sites_data,
#     }




# async def fetch_user_data(email: str, db: AsyncSession):
#     # Step 1: Fetch active sites
#     active_sites_response = await fetch_active_sites(email=email)

#     if active_sites_response["count"] == 0:
#         logging.warning("No sites found for the given email.")
#         return {
#             "sites_data": [],
#             "totals": {
#                 "total_sites": 0,
#                 "total_users": 0,
#                 "active_users": 0,
#                 "active_modules": 0,
#             }
#         }

#     # Extract all sites dynamically
#     sites = active_sites_response["sites"].get("sites", {}).get("message", [])
#     if not sites:
#         logging.warning("No sites found in the `message` key.")
#         return {
#             "sites_data": [],
#             "totals": {
#                 "total_sites": 0,
#                 "total_users": 0,
#                 "active_users": 0,
#                 "active_modules": 0,
#             }
#         }

#     # Initialize aggregated totals
#     total_users_count = 0
#     active_users_count = 0
#     active_modules_count = 0

#     # List to hold site-specific data
#     sites_data = []

#     headers = {
#         # "Authorization": f"token {API_KEY}:{API_SECRET}"
#     }

#     # Step 2: Loop through all sites and fetch data
#     async with httpx.AsyncClient() as client:
#         for site in sites:
#             site_name = site.get("site_name")
#             if not site_name:
#                 continue

#             # Define dynamic URLs
#             urls = {
#                 "total_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_users",
#                 "active_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_active_users",
#                 "active_modules": f"http://{site_name}/api/method/clientportalapp_admin.modules.get_modules"
#             }

#             try:
#                 # Fetch data from each site
#                 total_users_response = await client.get(urls["total_users"])
#                 total_users_response.raise_for_status()

#                 active_users_response = await client.get(urls["active_users"])
#                 active_users_response.raise_for_status()

#                 active_modules_response = await client.get(urls["active_modules"])
#                 active_modules_response.raise_for_status()

#                 # Parse responses
#                 total_users_data = total_users_response.json().get("message", {})
#                 active_users_data = active_users_response.json().get("message", {})
#                 active_modules_data = active_modules_response.json().get("message", {})

#                 # Update totals
#                 total_users_count += total_users_data.get("count", 0)
#                 active_users_count += active_users_data.get("count", 0)
#                 active_modules_count += active_modules_data.get("count", 0)
                
                
#                 result = await db.execute(select(User).filter(User.email == email))
#                 user = result.scalar_one_or_none() 

#                 # Add site-specific data to the list
#                 site_data = SiteData(
#                     site_name=site_name,
#                     total_users_count=total_users_count,
#                     active_users_count=active_users_count,
#                     active_modules_count=active_modules_count,
#                     #active_sites=active_sites_count,
#                     total_users=total_users_data.get("users", []),
#                     active_users=active_users_data.get("users", []),
#                     active_modules=active_modules_data.get("modules", []),
#                     sites_data={
#                         "total_users": total_users_data,
#                         "active_users": active_users_data,
#                         "active_modules": active_modules_data
#                     },
#                     user=user 
#                 )

#                 db.add(site_data)
#                 sites_data.append({
#                     "site_name": site_name,
#                     "total_users": {
#                         "count": total_users_data.get("count", 0),
#                         "users": total_users_data.get("users", [])
#                     },
#                     "active_users": {
#                         "count": active_users_data.get("count", 0),
#                         "users": active_users_data.get("users", [])
#                     },
#                     "active_modules": {
#                         "count": active_modules_data.get("count", 0),
#                         "modules": active_modules_data.get("modules", [])
#                     }
#                 })

#             except httpx.RequestError as e:
#                 logging.error(f"Request error on site {site_name}: {e}")
#             except httpx.HTTPStatusError as e:
#                 logging.error(f"HTTP error on site {site_name}: {e.response.status_code} - {e.response.text}")

#     # Commit the changes to the DB
#     await db.commit()

#     # Step 3: Return consolidated data
#     return {
#         "totals": {
#             "active_sites": len(sites),
#             "total_users": total_users_count,
#             "active_users": active_users_count,
#             "total_active_modules": active_modules_count,
#         },
#         "sites_data": sites_data,
#     }



# async def fetch_user_data(email: str, db: AsyncSession):
#     # Step 1: Fetch active sites (as before)
#     active_sites_response = await fetch_active_sites(email=email)

#     if active_sites_response["count"] == 0:
#         logging.warning("No sites found for the given email.")
#         return {
#             "sites_data": [],
#             "totals": {
#                 "total_sites": 0,
#                 "total_users": 0,
#                 "active_users": 0,
#                 "active_modules": 0,
#             }
#         }

#     # Extract all sites dynamically
#     sites = active_sites_response["sites"].get("sites", {}).get("message", [])
#     if not sites:
#         logging.warning("No sites found in the `message` key.")
#         return {
#             "sites_data": [],
#             "totals": {
#                 "total_sites": 0,
#                 "total_users": 0,
#                 "active_users": 0,
#                 "active_modules": 0,
#             }
#         }

#     # Initialize aggregated totals
#     total_users_count = 0
#     active_users_count = 0
#     active_modules_count = 0
#     active_sites_count = 0

#     # List to hold site-specific data
#     sites_data = []

#     # Step 2: Loop through all sites and fetch data
#     async with httpx.AsyncClient() as client:
#         for site in sites:
#             site_name = site.get("site_name")
#             if not site_name:
#                 continue

#             # Define dynamic URLs
#             urls = {
#                 "total_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_users",
#                 "active_users": f"http://{site_name}/api/method/clientportalapp_admin.users.get_active_users",
#                 "active_modules": f"http://{site_name}/api/method/clientportalapp_admin.modules.get_modules",
#                 "active_sites": f"http://{site_name}/api/method/clientportalapp_admin.sites.get_sites",
#             }

#             try:
#                 # Fetch data from each site
#                 total_users_response = await client.get(urls["total_users"])
#                 total_users_response.raise_for_status()

#                 active_users_response = await client.get(urls["active_users"])
#                 active_users_response.raise_for_status()

#                 active_modules_response = await client.get(urls["active_modules"])
#                 active_modules_response.raise_for_status()
                
#                 active_sites_response = await client.get(urls["active_sites"])

#                 # Parse responses
#                 total_users_data = total_users_response.json().get("message", {})
#                 active_users_data = active_users_response.json().get("message", {})
#                 active_modules_data = active_modules_response.json().get("message", {})
#                 active_sites_data = active_sites_response.json().get("message", {})

#                 # Update totals
#                 total_users_count += total_users_data.get("count", 0)
#                 active_users_count += active_users_data.get("count", 0)
#                 active_modules_count += active_modules_data.get("count", 0)
#                 active_sites_count += active_sites_data.get("count", 0)

#                 # Create SiteData instance
#                 # Assuming you have correctly imported SQLAlchemy classes
#                 from sqlalchemy.future import select

#                 result = await db.execute(select(User).filter(User.email == email))
#                 user = result.scalar_one_or_none()  # This is the correct usage of scalar_one_or_none() in SQLAlchemy


#                 site_data = SiteData(
#                     site_name=site_name,
#                     total_users_count=total_users_count,
#                     active_users_count=active_users_count,
#                     active_modules_count=active_modules_count,
#                     active_sites=active_sites_count,
#                     total_users=total_users_data.get("users", []),
#                     active_users=active_users_data.get("users", []),
#                     active_modules=active_modules_data.get("modules", []),
#                     sites_data={
#                         "total_users": total_users_data,
#                         "active_users": active_users_data,
#                         "active_modules": active_modules_data
#                     },
#                     user=user  # Associate the SiteData with the user
#                 )


#                 # Append site_data to the list
#                 sites_data.append(site_data)
                
#                 db.add(site_data)

#             except httpx.RequestError as e:
#                 logging.error(f"Request error on site {site_name}: {e}")
#             except httpx.HTTPStatusError as e:
#                 logging.error(f"HTTP error on site {site_name}: {e.response.status_code} - {e.response.text}")

#     # Commit the changes to the database (if necessary)
#     await db.commit()

#     # Step 3: Return consolidated data
#     return {
#         "totals": {
#             "active_sites": len(sites),
#             "total_users": total_users_count,
#             "active_users": active_users_count,
#             "total_active_modules": active_modules_count,
#         },
#         "sites_data": sites_data,
#     }

