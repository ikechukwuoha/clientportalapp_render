import json
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.database.db import get_db
from fastapi import APIRouter, Depends
from app.api.models.product import Product
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, APIRouter, Request
from app.api.schemas.product_schema import ItemUpdateRequest
from app.api.services.product_services import fetch_and_save_product, get_products

from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from app.api.services.product_services import update_item_in_frappe
import json

import logging
import traceback


logger = logging.getLogger(__name__)

router = APIRouter()


API_KEY = "e5c55a245ee4275"
API_SECRET = "272ba90f78ddcfa"

@router.get("/get-products", tags=["product"])
async def get_all_products(db: AsyncSession = Depends(get_db)):
    """
    Fetch products from the external API, save them to the database, and return formatted products.
    """
    return await get_products(db)


    
# routes/products.py
@router.get("/get-product/{name}", tags=["product"])
async def get_product(name: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch product details by name from the external API, save to database, and return formatted data.
    """
    product = await fetch_and_save_product(name, db)
    return product





@router.post("/get_data_from_erp")
async def get_data_from_erp(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        raw_body = await request.body()
        try:
            data_dict = json.loads(raw_body.decode())
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from the raw body")
            return JSONResponse(content={"message": "Invalid JSON payload"}, status_code=400)

        logger.info(f"Processing product: {data_dict.get('item_name')}")

        # Extract the product details
        item_code = data_dict.get("item_code")
        product_title = data_dict.get("item_name")
        product_image = data_dict.get("image")
        product_description = data_dict.get("description")
        standard_rate = data_dict.get("standard_rate", 0.0)

        # Check if the product already exists in the database by item_code
        query = select(Product).where(Product.product_code == item_code)
        result = await db.execute(query)
        existing_product = result.scalar_one_or_none()

        if existing_product:
            # Update the fields that have changed
            existing_product.product_title = product_title  # Ensure the name is updated
            existing_product.product_image = product_image
            
            # Update the product description only if it was provided
            if product_description is not None:
                existing_product.product_description = product_description

            # Optionally, update standard_rate if needed
            # existing_product.standard_rate = standard_rate

            logger.info(f"Updated product: {product_title} with item_code {item_code}")
        else:
            # Create a new product with or without a description
            new_product = Product(
                item_code=item_code,
                product_title=product_title,
                product_image=product_image,
                product_description=product_description,
                standard_rate=standard_rate
            )
            db.add(new_product)

            logger.info(f"Created new product: {product_title} with item_code {item_code}")

        # Commit the transaction
        await db.commit()
        return JSONResponse(content={"message": "Product processed successfully"}, status_code=200)

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        await db.rollback()
        return JSONResponse(content={"message": "Database error occurred"}, status_code=500)

    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)




@router.put("/update-item/")
def update_item(payload: ItemUpdateRequest):
    return update_item_in_frappe(payload)



























# @router.get("/get-product/{name}", tags=["product"])
# async def get_products(name: str, db: AsyncSession = Depends(get_db)):
#     # Format the URL with the product name
#     url = f"http://clientportal:8080/api/method/clientportalapp.products.get_product_pricing_by_idx?name={name}"

#     headers = {
#         "Authorization": f"token {API_KEY}:{API_SECRET}"
#     }

#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url, headers=headers)
#             response.raise_for_status()
#     except httpx.HTTPStatusError as exc:
#         raise HTTPException(status_code=exc.response.status_code, detail="Error fetching product")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     # Parse the JSON response
#     data = response.json()
#     product = data.get("message", {})

#     # Format the product data
#     formatted_product = {
#         "productId": product.get("name"),
#         "productName": product.get("item_name"),
#         "provider": product.get("item_group", "Unknown"),
#         "rating": product.get("rating", "N/A"),
#         "userCount": product.get("user_count", "N/A"),
#         "description": product.get("description"),
#         "imageSrc": product.get("images", []),
#     }
# # 
#     # Format the benefits
#     formatted_benefits = [
#         {
#             "title": benefit.get("title"),
#             "description": benefit.get("description")
#         }
#         for benefit in product.get("benefits", [])
#     ]

#     # Format the security details (if present)
#     formatted_security_details = [
#         {
#             "description": product.get("security", "No security details available")
#         }
#     ] if product.get("security") else []

#     # Format the services (if any)
#     formatted_services = [
#         {
#             "title": service.get("title"),
#             "description": service.get("description"),
#             "imageSrc": service.get("image", "")
#         }
#         for service in product.get("services", [])
#     ]

#     # Format the reviews (if any)
#     formatted_reviews = [
#         {
#             "name": review.get("name"),
#             "date": review.get("date"),
#             "description": review.get("description"),
#             "rating": review.get("rating"),
#             "image": review.get("image", "")
#         }
#         for review in product.get("reviews", [])
#     ]

#     # Plan details section
#     plan_details = [
#         {
#             "no_of_teamMembers": "1 - 10",
#             "cost": product.get("price", "Price not available"),
#             "billingCycle": "monthly"
#         }
#     ]

#     # Formatted overview
#     formatted_overview = {
#         "description": product.get("description"),
#         "imageSrc": product.get("images", []),
#         "benefits": formatted_benefits,
#         "securityDetails": formatted_security_details,
#     }

#     return {
#         "productId": product.get("name"),
#         "productName": product.get("item_name"),
#         "provider": product.get("item_group", "Unknown"),
#         "rating": product.get("rating", "N/A"),
#         "userCount": product.get("user_count", "N/A"),
#         "overview": formatted_overview,
#         "services": formatted_services,
#         "reviews": formatted_reviews,
#         "plan_details": plan_details
#     }



# from fastapi import APIRouter, Depends, HTTPException, Response, status
# from sqlalchemy.orm import Session
# from app.config.settings import settings
# from app.database.db import get_db
# from app.models.product import Product
# import httpx
# import uuid

# router = APIRouter()

# API_KEY = "7a6c5c848566ccb"
# API_SECRET = "e7438448e85099b"

# async def save_product_to_db(db: Session, product_data: dict):
#     db_product = Product(
#         id=uuid.uuid4(),
#         product_title=product_data.get("name"),
#         product_description=product_data.get("description"),
#         product_image=product_data.get("images", [None])[0],  # Use the first image, or None if empty
#         product_price=product_data.get("price")
#     )
#     db.add(db_product)
#     db.commit()
#     db.refresh(db_product)
#     return db_product

# @router.get("/products", tags=["product"])
# async def get_products():
#     url = "http://localhost:8000/api/method/clientportalapp.products.get_products_pricing"

#     headers = {
#         "Authorization": f"token {API_KEY}:{API_SECRET}"  
#     }

#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url, headers=headers)  # Add headers here
#             response.raise_for_status()  # Raise an exception for 4xx or 5xx responses
#     except httpx.HTTPStatusError as exc:
#         raise HTTPException(status_code=exc.response.status_code, detail="Error fetching products")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     # Parse the JSON response
#     data = response.json()
#     products = data.get("message", [])

#     # Format the products to include all images
#     formatted_products = [
#         {
#             "productId": product.get("name"),
#             "productName": product.get("name"),
#             "provider": product.get("name"),
#             "rating": product.get("name"),
#             "userCount": product.get("name"),
#             "description": product.get("description"),
#             "imageSrc": product.get("images", []),  
#         }
#         for product in products
#     ]

#     formatted_benefits = [
#         {
#             "title": product.get("name"),
#             "description": product.get("description")
#         }
#         for product in products
#     ]

#     formatted_security_details = [
#         {
#             "description": product.get("description"),
#         }
#         for product in products
#     ]

#     formatted_services = [
#         {
#             "title": product.get("name"),
#             "description": product.get("description"),
#             "imageSrc": product.get("image"),  
#         }
#         for product in products
#     ]

#     formatted_reviews = [
#         {
#             "name": product.get("name"),
#             "date": product.get("name"),
#             "description": product.get("description"),
#             "rating": product.get("description"),
#             "image": product.get("image"),
#         }
#         for product in products
#     ]

#     plan_details = [
#         {
#             "no_of_teamMembers": "1 -10",
#             "cost": product.get("price", "Price not available"),
#             "billingCyle": "monthly",
#         }
#         for product in products
#     ]

#      # Save to DB
#     await save_product_to_db(db, product_data)

#     return {
#             "overview": formatted_products,
#             "benefits": formatted_benefits,
#             "securityDetails": formatted_security_details,
#             "services": formatted_services,
#             "reviews": formatted_reviews,
#             "plan_details": plan_details,
#             }


# @router.get("/products", tags=["product"])
# async def get_products():
#     url = "http://localhost:8000/api/method/clientportalapp.products.get_products_pricing"

#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url)
#             response.raise_for_status()  # Raise an exception for 4xx or 5xx responses
#     except httpx.HTTPStatusError as exc:
#         raise HTTPException(status_code=exc.response.status_code, detail="Error fetching products")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     # Parse the JSON response
#     data = response.json()
#     products = data.get("message", [])

#     # Format the products to include all images
#     formatted_products = [
#         {
#             "name": product.get("name"),
#             "item_name": product.get("item_name"),
#             "item_group": product.get("item_group"),
#             "description": product.get("description"),
#             "images": product.get("images", []),  # Get all images as an array
#             "price": product.get("price", "Price not available")  # Handle null price
#         }
#         for product in products
#     ]

#     return {"products": formatted_products}