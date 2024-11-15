from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.config.settings import settings
from app.api.database.db import get_db
from app.api.models.product import Product
import httpx
import uuid

router = APIRouter()

API_KEY = "7a6c5c848566ccb"
API_SECRET = "2c2b90c8069052e"

async def save_product_to_db(db: AsyncSession, product_data: dict):
    # Check if product already exists to avoid duplicates
    query = select(Product).where(Product.product_title == product_data.get("name"))
    result = await db.execute(query)
    existing_product = result.scalars().first()

    if not existing_product:
        images = product_data.get("images", [])
        product_image = images[0] if images else None

        # Create and save the product in the database
        db_product = Product(
            id=uuid.uuid4(),
            product_title=product_data.get("name"),
            product_description=product_data.get("description"),
            product_image=product_image,
        )
        db.add(db_product)
        await db.commit()
        await db.refresh(db_product)
        return db_product
    return existing_product

@router.get("/get-products", tags=["product"])
async def get_all_products_services(db: AsyncSession = Depends(get_db)):
    url = "http://localhost:8000/api/method/clientportalapp.products.get_products_pricing"
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}"  
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="Error fetching products")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Parse the JSON response
    data = response.json()
    products = data.get("message", [])

    # Format products with images and save each one to the database
    formatted_products = []
    for idx, product in enumerate(products, start=1):
        formatted_product = {
            "id": idx,  # Or use product.get("name") if unique
            "title": product.get("name"),
            "shortDescription": product.get("description"),
            "longDescription": product.get("description"),
            "images": product.get("images", []),
            "buttons": [
                {"name": "Learn More", "styles": "button-style-purple"},
                {"name": "Add to Cart", "styles": "button-style-purple"},
                {"name": "Order Now", "styles": "button-style-purple"},
            ]
        }
        formatted_products.append(formatted_product)

    return formatted_products
    

@router.get("/get-product/{name}", tags=["product"])
async def get_products(name: str, db: AsyncSession = Depends(get_db)):
    # Format the URL with the product name
    url = f"http://localhost:8000/api/method/clientportalapp.products.get_product_pricing_by_idx?name={name}"

    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="Error fetching product")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Parse the JSON response
    data = response.json()
    product = data.get("message", {})

    # Format the product data
    formatted_product = {
        "productId": product.get("name"),
        "productName": product.get("item_name"),
        "provider": product.get("item_group", "Unknown"),
        "rating": product.get("rating", "N/A"),
        "userCount": product.get("user_count", "N/A"),
        "description": product.get("description"),
        "imageSrc": product.get("images", []),
    }
# 
    # Format the benefits
    formatted_benefits = [
        {
            "title": benefit.get("title"),
            "description": benefit.get("description")
        }
        for benefit in product.get("benefits", [])
    ]

    # Format the security details (if present)
    formatted_security_details = [
        {
            "description": product.get("security", "No security details available")
        }
    ] if product.get("security") else []

    # Format the services (if any)
    formatted_services = [
        {
            "title": service.get("title"),
            "description": service.get("description"),
            "imageSrc": service.get("image", "")
        }
        for service in product.get("services", [])
    ]

    # Format the reviews (if any)
    formatted_reviews = [
        {
            "name": review.get("name"),
            "date": review.get("date"),
            "description": review.get("description"),
            "rating": review.get("rating"),
            "image": review.get("image", "")
        }
        for review in product.get("reviews", [])
    ]

    # Plan details section
    plan_details = [
        {
            "no_of_teamMembers": "1 - 10",
            "cost": product.get("price", "Price not available"),
            "billingCycle": "monthly"
        }
    ]

    # Formatted overview
    formatted_overview = {
        "description": product.get("description"),
        "imageSrc": product.get("images", []),
        "benefits": formatted_benefits,
        "securityDetails": formatted_security_details,
    }

    return {
        "productId": product.get("name"),
        "productName": product.get("item_name"),
        "provider": product.get("item_group", "Unknown"),
        "rating": product.get("rating", "N/A"),
        "userCount": product.get("user_count", "N/A"),
        "overview": formatted_overview,
        "services": formatted_services,
        "reviews": formatted_reviews,
        "plan_details": plan_details
    }



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