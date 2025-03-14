import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.models.product import Product
import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import requests
from app.api.config.erp_config import FRAPPE_BASE_URL, HEADERS
from app.api.schemas.product_schema import ItemUpdateRequest
import logging





logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("product_fetch.log"),
        logging.StreamHandler()
    ]
)



async def fetch_and_save_product(db: AsyncSession) -> dict:
    url = f"{FRAPPE_BASE_URL}/api/method/clientportalapp.products.get_products_pricing"
    product_data = []

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            response_json = response.json()
            product_data = response_json.get("message", {}).get("items", [])
        except httpx.HTTPStatusError as exc:
            logging.error(f"HTTP error details: {exc.response.text}")
            return {"message": "Error fetching products", "products": []}
        except Exception as e:
            logging.error(f"Unable to fetch product data: {str(e)}")
            return {"message": "Error fetching products", "products": []}

    if not product_data:
        logging.warning("No products fetched from API.")
        return {"message": "No products found", "products": []}

    updated_products = []

    for item in product_data:
        # Directly use the plans data structure from the API response
        formatted_product = {
            "product_id": item.get("name"),
            "product_name": item.get("item_name"),
            "item_group": item.get("item_group", "Unknown"),
            "product_description": item.get("description", "No description provided."),
            "product_image": item.get("images", [None])[0],
            "images": item.get("images", []),
            "benefits": item.get("benefits", []),
            "plans": item.get("plans", {})  # Store the entire plans object directly
        }

        query = select(Product).where(Product.product_code == formatted_product["product_id"])
        result = await db.execute(query)
        existing_product = result.scalars().first()

        if not existing_product:
            new_product = Product(
                id=uuid.uuid4(),
                product_code=formatted_product["product_id"],
                product_title=formatted_product["product_name"],
                item_group=formatted_product["item_group"],
                product_description=formatted_product["product_description"],
                product_image=formatted_product["product_image"],
                images=formatted_product["images"],
                benefits=formatted_product["benefits"],
                plans=formatted_product["plans"]  # Store plans directly
            )
            db.add(new_product)
            updated_products.append(new_product)
        else:
            existing_product.product_title = formatted_product["product_name"]
            existing_product.item_group = formatted_product["item_group"]
            existing_product.product_description = formatted_product["product_description"]
            existing_product.product_image = formatted_product["product_image"]
            existing_product.images = formatted_product["images"]
            existing_product.benefits = formatted_product["benefits"]
            existing_product.plans = formatted_product["plans"]  # Update plans directly
            updated_products.append(existing_product)

    try:
        await db.commit()
    except Exception as e:
        logging.error(f"Error committing to database: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error saving products to database")

    # Return the products with the complete plans structure
    response_products = [
        {
            "id": str(product.id),
            "product_code": product.product_code,
            "product_title": product.product_title,
            "item_group": product.item_group,
            "product_description": product.product_description,
            "product_image": product.product_image,
            "images": product.images,
            "benefits": product.benefits,
            "plans": product.plans  # Return the complete plans object
        }
        for product in updated_products
    ]

    return {"message": "Products fetched successfully", "products": response_products}



async def fetch_products_from_db(db: AsyncSession) -> dict:
    """
    Fetch products from the database without updating from API.
    """
    try:
        # Fetch all products from database
        query = select(Product)
        result = await db.execute(query)
        products = result.scalars().all()

        if not products:
            return {"message": "No products found in database", "products": []}

        # Prepare response with products directly from database
        response_products = []
        for product in products:
            response_products.append({
                "id": str(product.id),
                "product_code": product.product_code,
                "product_title": product.product_title,
                "item_group": product.item_group,
                "product_description": product.product_description,
                "product_image": product.product_image,
                "images": product.images,
                "benefits": product.benefits,
                "plans": product.plans
            })

        return {
            "message": "Products fetched successfully", 
            "products": response_products
        }
    except Exception as e:
        logging.error(f"Error fetching products from database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching products from database"
        )


async def fetch_single_product_from_db(product_id: uuid.UUID, db: AsyncSession) -> dict:
    """
    Fetch a single product from database and update it with latest API data if available.
    """
    try:
        # First, fetch the specific product from database
        query = select(Product).where(Product.id == product_id)
        result = await db.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {product_id} not found"
            )

        # Create base response with existing plans
        response_product = {
            "id": str(product.id),
            "product_code": product.product_code,
            "product_title": product.product_title,
            "item_group": getattr(product, 'item_group', None),
            "product_description": product.product_description,
            "product_image": product.product_image,
            "images": getattr(product, 'images', []),
            "benefits": getattr(product, 'benefits', []),
            "plans": product.plans if product.plans else {}
        }

        # Attempt to fetch latest data from API
        url = f"{FRAPPE_BASE_URL}/api/method/clientportalapp.products.get_products_pricing"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                api_product_data = response.json().get("message", {}).get("items", [])

                # Find matching product in API data
                matching_api_product = next(
                    (item for item in api_product_data if item.get("name") == product.product_code),
                    None
                )

                if matching_api_product:
                    # Update product in database with new data
                    product.product_title = matching_api_product.get("item_name", product.product_title)
                    product.item_group = matching_api_product.get("item_group", getattr(product, 'item_group', None))
                    product.product_description = matching_api_product.get("description", product.product_description)
                    product.product_image = matching_api_product.get("images", [product.product_image])[0]
                    product.images = matching_api_product.get("images", getattr(product, 'images', []))
                    product.benefits = matching_api_product.get("benefits", getattr(product, 'benefits', []))
                    product.plans = matching_api_product.get("grouped_data", product.plans)
                    
                    await db.commit()

                    # Update response with new data
                    response_product.update({
                        "product_title": product.product_title,
                        "item_group": product.item_group,
                        "product_description": product.product_description,
                        "product_image": product.product_image,
                        "images": product.images,
                        "benefits": product.benefits,
                        "plans": product.plans
                    })

        except Exception as e:
            logging.warning(f"API fetch failed, using existing database product: {str(e)}")

        return {
            "message": "Product found",
            "product": response_product
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in fetch_single_product_from_db: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching product data"
        )



# This Function will be used to update a doctype in frappe I.e the site doctype when a user purchases an item
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
            f"{FRAPPE_BASE_URL}/api/method/clientportalapp.product.update_item_from_api/{payload.name}",
            json=item_data,
             headers = {
            # "Authorization": f"token {API_KEY}:{API_SECRET}"
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
                    f"{FRAPPE_BASE_URL}/api/resource/Benefits",
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
                    f"{FRAPPE_BASE_URL}/api/resource/ItemImage",
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
                f"{FRAPPE_BASE_URL}/api/resource/Item Price",
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
    
    
    










# async def fetch_and_save_product(db: AsyncSession) -> dict:
#     """
#     Fetch product data from the Frappe API, format it, and save it to the database.
#     """
#     url = f"{FRAPPE_BASE_URL}/api/method/clientportalapp.products.get_products_pricing"

#     # Fetch product data from the API
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(url)
#             response.raise_for_status()
#             product_data = response.json().get("message", {}).get("items", [])
#         except httpx.HTTPStatusError as exc:
#             logging.error(f"HTTP error while fetching product: {exc.response.status_code} - {exc.response.text}")
#             raise HTTPException(status_code=exc.response.status_code, detail="Error fetching product")
#         except Exception as e:
#             logging.error(f"Unexpected error: {str(e)}")
#             raise HTTPException(status_code=500, detail=str(e))

  
#     updated_products = []

#     for item in product_data:
#         plans = {}
#         for plan_name in ["Standard Plan", "Custom Plan", "Free Plan"]:
#             plan_descriptions = item.get("plan_descriptions", {})
#             plan_items = plan_descriptions.get(plan_name, [])
#             descriptions = [desc.get("description") for desc in plan_items]

            
#             plan_pricing = item.get("prices", {}).get(plan_name, {}).copy() 

           
#             if plan_name == "Standard Plan":
#                 # Remove custom_rate from the "Standard Plan"
#                 plan_pricing.pop("custom_rate", None)
#                 plan_pricing.pop("custom_training_and_setup", None)
#                 plan_pricing.pop("price_list_rate", None)

#             elif plan_name == "Custom Plan":
#                 # Remove standard_rate from the "Custom Plan"
#                 plan_pricing.pop("standard_rate", None)
#                 plan_pricing.pop("standard_training_and_setup", None)
#                 plan_pricing.pop("price_list_rate", None)

#             elif plan_name == "Free Plan":
#                 # Remove both standard_rate and custom_rate from the "Free Plan"
#                 plan_pricing.pop("standard_rate", None)
#                 plan_pricing.pop("custom_rate", None)
#                 plan_pricing.pop("standard_training_and_setup", None)
#                 plan_pricing.pop("custom_training_and_setup", None)
#                 plan_pricing.pop("price_list_rate", None)

#             # Add the modified plan data to the plans dictionary
#             plans[plan_name] = {
#                 "description": descriptions,
#                 "pricing": plan_pricing
#             }

#         #print(f"Plans for Product {item.get('name')}: {plans}") 

        
#         formatted_product = {
#             "product_id": item.get("name"),
#             "product_name": item.get("item_name"),
#             "item_group": item.get("item_group", "Unknown"),
#             "product_description": item.get("description", "No description provided."),
#             "product_image": item.get("images", [None])[0],
#             "images": item.get("images", []),
#             "benefits": item.get("benefits", []),
#             "plans": plans,
#         }

#         # Check if the product already exists in the database
#         query = select(Product).where(Product.product_code == formatted_product["product_id"])
#         result = await db.execute(query)
#         existing_product = result.scalars().first()

#         if not existing_product:
#             new_product = Product(
#                 id=uuid.uuid4(),
#                 product_code=formatted_product["product_id"],
#                 product_title=formatted_product["product_name"],
#                 item_group=formatted_product["item_group"],
#                 product_description=formatted_product["product_description"],
#                 product_image=formatted_product["product_image"],
#                 images=formatted_product["images"],
#                 benefits=formatted_product["benefits"],
#                 plans=formatted_product["plans"],
#             )
#             db.add(new_product)
#             updated_products.append(new_product)
#         else:
           
#             existing_product.product_title = formatted_product["product_name"]
#             existing_product.item_group = formatted_product["item_group"]
#             existing_product.product_description = formatted_product["product_description"]
#             existing_product.product_image = formatted_product["product_image"]
#             existing_product.images = formatted_product["images"]
#             existing_product.benefits = formatted_product["benefits"]
#             existing_product.plans = formatted_product["plans"]
#             updated_products.append(existing_product)

#         await db.commit()

#         # Serialize products for response
#         response_products = [
#             {
#                 "id": str(product.id),
#                 "product_code": product.product_code,
#                 "product_title": product.product_title,
#                 "item_group": product.item_group,
#                 "product_description": product.product_description,
#                 "product_image": product.product_image,
#                 "images": product.images,
#                 "benefits": product.benefits,
#                 "plans": {
#                     plan_name: {
#                         "description": plan["description"],
#                         "pricing": plan["pricing"]
#                     }
#                     for plan_name, plan in product.plans.items()
#                 },
#             }
#             for product in updated_products
#         ]

#         return {"message": "Product Fetched successfully ", "products": response_products}