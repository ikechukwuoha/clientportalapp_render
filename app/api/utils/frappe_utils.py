import json
from fastapi import HTTPException
import httpx
import logging
from app.api.config.erp_config import FRAPPE_BASE_URL

# Define these at the top of your file

FRAPPE_SITE_CREATE_ENDPOINT = f"{FRAPPE_BASE_URL}/api/method/admin_clientportalapp.site_manager_app.create_new_site"
FRAPPE_STORE_SITE_ENDPOINT = f"{FRAPPE_BASE_URL}/api/method/admin_clientportalapp.sites.save_site"





async def store_site_data(site_data):
    headers = {
        "Content-Type": "application/json"
    }
    
    logging.info(f"Attempting to store site data for site: {site_data.get('site_name')}")
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            logging.info(f"Making request to: {FRAPPE_STORE_SITE_ENDPOINT}")
            logging.info(f"Request payload: {json.dumps(site_data)}")
            
            response = await client.post(
                FRAPPE_STORE_SITE_ENDPOINT,
                json=site_data,
                headers=headers
            )
            
            logging.info(f"Response status: {response.status_code}")
            logging.info(f"Response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
    except httpx.RequestError as e:
        error_msg = f"Network error when storing site data: {str(e)}"
        logging.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
        
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error when storing site data: {e.response.status_code} - {e.response.text}"
        logging.error(error_msg)
        raise HTTPException(status_code=e.response.status_code, detail=error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error when storing site data: {str(e)}"
        logging.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
    


async def create_frappe_site(site_name: str, plan: str, quantity: int):
    # Create a new Frappe site using the existing site creation endpoint.
  
    
    # Ensure site name ends with .purpledove.net
    if not site_name.endswith('erp.staging.purpledove.net'):
        site_name = f"{site_name}erp.staging.purpledove.net"
    
    site_data = {
        "site_name": site_name,
        "plan": plan,
        "user_count": quantity
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        logging.info(f"Initiating Frappe site creation for: {site_name}")
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                f"{FRAPPE_SITE_CREATE_ENDPOINT}",
                json=site_data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Error creating Frappe site: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Frappe site: {str(e)}"
        )
        
        
        
        
        
        
        
        

# FRAPPE_API_KEY = "7a6c5c848566ccb"
# FRAPPE_API_SECRET = "eb1eb590370070d"

# async def store_site_data(site_data):
#     headers = {
#         # "Authorization": f"token {FRAPPE_API_KEY}:{FRAPPE_API_SECRET}",
#         "Content-Type": "application/json"
#     }

#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.post(FRAPPE_URL, json=site_data, headers=headers)
#             response.raise_for_status()
#             print("THIS IS FRAPPE UPDATIMG RESPONSE22222222222222222222222222222222222222222222222222222222222222222222", response)
#             return response.json()

#     except httpx.RequestError as e:
#         logging.error(f"Request error: {e}")
#         raise

#     except httpx.HTTPStatusError as e:
#         logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
#         raise


