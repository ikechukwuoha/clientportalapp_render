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
    
    


async def create_frappe_site(site_data: dict):
    headers = {
        "Content-Type": "application/json"
    }

    try:
        logging.info(f"Starting Frappe site creation with data: {site_data}")

        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.post(FRAPPE_URL12, json=site_data, headers=headers)
            logging.debug(f"Response Status Code: {response.status_code}")
            logging.debug(f"Response Body: {response.text}")

            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
            logging.debug(f"Response JSON: {data}")

            if data.get("status") == "error":
                logging.error(f"Frappe API returned an error: {data.get('message')}")
                raise HTTPException(status_code=400, detail=data.get("message"))

            logging.info("Frappe site created successfully.")

            # Now, add logging for the next steps, especially after this point
            logging.info(f"Site creation completed, now proceeding with next steps.")
            
            # Add other actions here after Frappe site creation
            return data

    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error connecting to the Frappe API."
        )
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=500,
            detail="Frappe API returned an error."
        )
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during site creation."
        )
