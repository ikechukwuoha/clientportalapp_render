from fastapi import HTTPException
import httpx
import logging

FRAPPE_URL = "http://clientportal.org:8080/api/method/clientportalapp_admin.sites.save_site"

FRAPPE_URL12 = "http://clientportal.org:8080/api/method/clientportalapp_admin.sites.create_new_site"
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




async def store_site_data(site_data):
    headers = {
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(FRAPPE_URL, json=site_data, headers=headers)
            response.raise_for_status()
            
            # Print both status code and response content
            print("Status Code:", response.status_code)
            print("Response Content:", response.text)
            
            return response.json()

    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        raise
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    
    


async def create_frappe_site(site_name: str):
    """
    Create a new Frappe site using the existing site creation endpoint.
    Ensures the site name has the correct domain suffix.
    """
    # Format site name if needed
    if not site_name.endswith('.purpledove.net'):
        site_name = f"{site_name}.purpledove.net"
    
    site_data = {
        "site_name": site_name,
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        logging.info(f"Initiating Frappe site creation for: {site_name}")
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                f"{FRAPPE_URL}/api/method/clientportalapp_admin.site_manager_app.create_new_site",
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