from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.models.cart import Cart, CartItem
from app.api.models.product import Product
from uuid import uuid4
from sqlalchemy import type_coerce
from sqlalchemy import cast
from sqlalchemy import String

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)




async def add_item_to_cart(db: AsyncSession, user_id: UUID, product_id: str, quantity: int = 1):
    # Find the user's cart
    result = await db.execute(select(Cart).filter(cast(Cart.user_id, String) == str(user_id)))
    cart = result.scalars().first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found for the user.")

    # Check if the item already exists in the cart
    result = await db.execute(
        select(CartItem).filter(CartItem.cart_id == cart.id, CartItem.item_id == product_id)
    )
    cart_item = result.scalars().first()

    if cart_item:
        # Update quantity if item exists
        cart_item.quantity += quantity
    else:
        # Fetch the product details to get title, descriptions, and images
        result = await db.execute(select(Product).filter(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        
        # Add a new item to the cart, including product details
        new_cart_item = CartItem(
            id=uuid4(),
            cart_id=cart.id,
            item_id=product.id,
            title=product.product_title,
            price=product.product_price,
            quantity=quantity,
            short_description=product.product_description,
            long_description=product.product_description,
            images=product.product_image
        )
        db.add(new_cart_item)

    await db.commit()
    return {"message": "Item added to cart successfully."}





async def remove_item_from_cart(db: AsyncSession, user_id: str, product_id: str):
    # Find the user's cart
    result = await db.execute(select(Cart).filter(Cart.user_id == user_id))
    cart = result.scalars().first()
    if not cart:
        raise ValueError("Cart not found for the user.")

    # Check if the item exists in the cart
    result = await db.execute(
        select(CartItem).filter(CartItem.cart_id == cart.id, CartItem.item_id == product_id)
    )
    cart_item = result.scalars().first()
    if not cart_item:
        raise ValueError("Item not found in cart.")

    # Remove the item
    await db.delete(cart_item)
    await db.commit()
    return {"message": "Item removed from cart successfully."}




async def view_cart(db: AsyncSession, user_id: str):
    logger = logging.getLogger(__name__)

    try:
        # Ensure the user_id is a UUID object
        user_id = str(user_id) if isinstance(user_id, UUID) else user_id
        logger.debug(f"Searching for cart with user_id: {user_id}")

        # Find the user's cart
        result = await db.execute(select(Cart).filter(Cart.user_id == user_id))
        cart = result.scalars().first()

        if not cart:
            logger.warning(f"No cart found for user_id: {user_id}")
            raise ValueError("Cart not found for the user.")

        logger.debug(f"Cart found: {cart.id}")

        result = await db.execute(
            select(CartItem)
            .filter(CartItem.cart_id == cart.id)
            .options(selectinload(CartItem.product))
        )
        
        cart_items = result.scalars().all()
        logger.debug(f"Cart items fetched: {cart_items}")

        logger.debug(f"Cart contains {len(cart_items)} items.")

        # Calculate total cost by summing the price * quantity for each item
        total_cost = sum(item.price * item.quantity for item in cart_items)
        logger.info(f"Total cost calculated: {total_cost}")

        # Log the prices for each item in the cart
        # for item in cart_items:
        #     logger.debug(f"Item ID: {item.item_id}, Price: {item.price}, Quantity: {item.quantity}")
        
        for item in cart_items:
            logger.debug(f"Item ID: {item.item_id}, Price: {item.price}")



        # Prepare the response
        response = {
            "cart_id": cart.id,
            "items": [
                {
                    "item_id": item.item_id,
                    "quantity": item.quantity,
                    "title": item.title,
                    "shortDescription": item.short_description,
                    "longDescription": item.long_description,
                    "price": item.price,
                    "total_price": item.price * item.quantity,
                    "images": item.images,
                }
                for item in cart_items
            ],
            "total_cost": total_cost,
        }


        logger.debug(f"Response prepared: {response}")

        # Return the response
        return response

    except Exception as e:
        logger.error(f"Error preparing response: {e}")
        raise






async def checkout(db: AsyncSession, user_id: str):
    result = await db.execute(select(Cart).filter(Cart.user_id == user_id))
    cart = result.scalars().first()
    if not cart:
        raise ValueError("Cart not found for the user.")

    result = await db.execute(
        select(CartItem).filter(CartItem.cart_id == cart.id).options(selectinload(CartItem.product))
    )
    cart_items = result.scalars().all()
    if not cart_items:
        raise ValueError("Cart is empty.")

    total_price = sum(item.price * item.quantity for item in cart_items)

    # Clear the cart after successful payment
    for item in cart_items:
        await db.delete(item)
    await db.commit()

    return {"message": "Checkout successful.", "total_price": total_price}





async def update_item_quantity(db: AsyncSession, user_id: str, product_id: str, quantity: int):
    if quantity <= 0:
        return await remove_item_from_cart(db, user_id, product_id)

    # Find the user's cart
    result = await db.execute(select(Cart).filter(Cart.user_id == user_id))
    cart = result.scalars().first()
    if not cart:
        raise ValueError("Cart not found for the user.")

    # Find the item in the cart
    result = await db.execute(
        select(CartItem).filter(CartItem.cart_id == cart.id, CartItem.item_id == product_id)
    )
    cart_item = result.scalars().first()
    if not cart_item:
        raise ValueError("Item not found in cart.")

    # Update the item's quantity
    cart_item.quantity = quantity
    await db.commit()
    return {"message": "Item quantity updated successfully."}
