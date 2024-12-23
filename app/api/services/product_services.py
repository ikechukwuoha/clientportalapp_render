import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.models.product import Product
import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

import requests
from app.api.config.erp_config import FRAPPE_URL, HEADERS

from app.api.schemas.product_schema import ItemUpdateRequest


import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Adjust to DEBUG for more detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("product_fetch.log"),  # Logs to a file
        logging.StreamHandler()  # Also outputs logs to the console
    ]
)



API_KEY = "d353644b94687d8"
API_SECRET = "486cd7c1107edc12"

async def fetch_products_from_api(client, url, headers):
    """
    Fetch products from the external API.
    """
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="Error fetching products")
    except httpx.RequestError as exc:
        error_message = f"Request failed: {str(exc)}"
        error_traceback = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"{error_message}\nTraceback: {error_traceback}"
        )
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        error_traceback = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"{error_message}\nTraceback: {error_traceback}"
        )
        
        
        
        
        
async def save_product_to_db(db: AsyncSession, product_data: dict):
    """
    Save a product to the database if it does not already exist.
    """

    # Log the type and content of product_data
    logger.debug(f"product_data type: {type(product_data)}")
    logger.debug(f"product_data content: {product_data}")

    # Validate product_data
    if not isinstance(product_data, dict):
        raise ValueError("product_data must be a dictionary")

    # Extract product fields with default values
    product_code = product_data.get("name")
    if not product_code:
        raise ValueError("Product data must include a 'name' field.")
    
    item_name = product_data.get("item_name", "Untitled Product")
    description = product_data.get("description", "No description provided.")
    price = product_data.get("price", 0.0)
    images = product_data.get("images", [])
    product_image = images[0] if images else None

    # Check if the product already exists
    query = select(Product).where(Product.product_code == product_code)
    result = await db.execute(query)
    existing_product = result.scalars().first()

    if existing_product:
        return existing_product

    # Create a new product
    db_product = Product(
        id=uuid.uuid4(),
        product_code=product_code,
        product_title=item_name,
        product_description=description,
        product_image=product_image,
        product_price=price,
    )
    
    try:
        db.add(db_product)
        await db.commit()
        await db.refresh(db_product)
        return db_product
    except Exception as e:
        await db.rollback()
        raise RuntimeError(f"Failed to save product: {e}")




async def process_products(db: AsyncSession, products: list):
    """
    Process each product, save to the database, and format for response.
    """
    formatted_products = []
    for idx, product in enumerate(products, start=1):
        # Save product to the database
        saved_product = await save_product_to_db(db, product)

        # Format the product for response
        formatted_product = {
            "id": idx, 
            "product Code": product.get("name"),
            "title": product.get("item_name"),
            "short Description": product.get("description"),
            "long Description": product.get("description"),
            "images": product.get("images", []),
            #"price": product.get("price"),
            # "standard price": product.get("standard_rate"),
            # "custom price": product.get("custom_rate"),
            # "standard_training_and_setup": product.get("standard_training_and_setup"),
            # "custom_training_and_setup": product.get("custom_training_and_setup")
        }
        formatted_products.append(formatted_product)
    return formatted_products




async def get_products(db: AsyncSession):
    """
    Orchestrate the fetching, processing, and saving of products.
    """
    url = "http://clientportal.org:8080/api/method/clientportalapp.products.get_products_pricing"
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}"
    }

    async with httpx.AsyncClient() as client:
        data = await fetch_products_from_api(client, url, headers)

    products = data.get("message", [])
    return await process_products(db, products)









API_KEY = "d353644b94687d8"
API_SECRET = "b5cb8b2a4e87792"

async def fetch_product_from_api(name: str) -> dict:
    """
    Fetch product data from the external API by name.
    """
    url = f"http://clientportal.org:8080/api/method/clientportalapp.products.get_product_pricing_by_idx?name={name}"
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logging.error(f"HTTP error while fetching product: {exc.response.status_code} - {exc.response.text}")
        raise HTTPException(status_code=exc.response.status_code, detail="Error fetching product")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    # Log the fetched product (pretty-printed JSON)
    product_data = response.json()
    logging.info(f"Fetched product data for '{name}':\n{json.dumps(product_data, indent=4)}")

    return product_data






async def format_product_data(product: dict) -> dict:
    """
    Format the product data fetched from the API.
    """
    formatted_product = {
        "productId": product.get("name"),
        "productName": product.get("item_name"),
        "provider": product.get("item_group", "Unknown"),
        "rating": product.get("rating", "N/A"),
        "userCount": product.get("user_count", "N/A"),
        "overview": {
            "description": product.get("description"),
            "imageSrc": product.get("images", []),
            "benefits": [
                {"title": benefit.get("title"), "description": benefit.get("description")}
                for benefit in product.get("benefits", [])
            ],
            "securityDetails": [
                {"description": product.get("security", "No security details available")}
            ] if product.get("security") else []
        },
        "services": [
            {
                "title": service.get("title"),
                "description": service.get("description"),
                "imageSrc": service.get("image", "")
            }
            for service in product.get("services", [])
        ],
        "reviews": [
            {
                "name": review.get("name"),
                "date": review.get("date"),
                "description": review.get("description"),
                "rating": review.get("rating"),
                "image": review.get("image", "")
            }
            for review in product.get("reviews", [])
        ],
        "pricing_details": [
            {
                #"no_of_teamMembers": "1 - 10",
                #"cost": product.get("price", "Price not available"),
                "standard_rate": product.get("standard_rate"),
                "custom_rate": product.get("custom_rate"),
                "standard_training_and_setup": product.get("standard_training_and_setup"),
                "custom_training_and_setup": product.get("custom_training_and_setup"),
                "billingCycle": "yearly"
            }
        ]
    }
    return formatted_product





async def fetch_and_save_product(name: str, db: AsyncSession) -> dict:
    """
    Fetch product data from the API, format it, and optionally save it to the database.
    """
    api_response = await fetch_product_from_api(name)
    product = api_response.get("message", {})

    # Save product to the database (if needed)
    await save_product_to_db(db, product)

    # Format the product for the response
    return await format_product_data(product)




def update_item_in_frappe(payload: ItemUpdateRequest):
    # Update the Item Doctype in Frappe
    item_data = {
        "item_name": payload.item_name,
        "item_group": payload.item_group,
        "description": payload.description,
        "custom_security": payload.custom_security
    }

    try:
        # Update the main Item record
        item_response = requests.put(
            f"{FRAPPE_URL}/api/method/clientportalapp.product.update_item_from_api/{payload.name}",
            json=item_data,
             headers = {
            "Authorization": f"token {API_KEY}:{API_SECRET}"
            }
        )

        if item_response.status_code != 200:
            raise HTTPException(
                status_code=item_response.status_code,
                detail=f"Failed to update Item: {item_response.json()}"
            )

        # Update Benefits child table
        if payload.benefits:
            for benefit in payload.benefits:
                response = requests.post(
                    f"{FRAPPE_URL}/api/resource/Benefits",
                    json={"parent": payload.name, **benefit},
                    headers=HEADERS
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to update Benefits: {response.json()}"
                    )

        # Update ItemImage child table
        if payload.images:
            for image in payload.images:
                response = requests.post(
                    f"{FRAPPE_URL}/api/resource/ItemImage",
                    json={"parent": payload.name, "images": image},
                    headers=HEADERS
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to update ItemImage: {response.json()}"
                    )

        # Update or add Item Price
        if payload.price is not None:
            response = requests.post(
                f"{FRAPPE_URL}/api/resource/Item Price",
                json={
                    "item_code": payload.name,
                    "price_list_rate": payload.price,
                    "valid_from": "2024-11-27"  # Example current date
                },
                headers=HEADERS
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to update Item Price: {response.json()}"
                )

        return {"message": "Item updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")