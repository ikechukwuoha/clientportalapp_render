from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.models.cart import Cart, CartItem
from app.api.models.product import Product
from uuid import uuid4
from sqlalchemy import type_coerce
from sqlalchemy import cast
from sqlalchemy import String



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
    # Find the user's cart
    result = await db.execute(select(Cart).filter(Cart.user_id == user_id))
    cart = result.scalars().first()
    if not cart:
        raise ValueError("Cart not found for the user.")

    # Retrieve all items in the cart with product details
    result = await db.execute(
        select(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .options(selectinload(CartItem.product))
    )
    cart_items = result.scalars().all()
    return {
        "cart_id": cart.id,
        "items": [
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
                "title": item.title,
                "shortDescription": item.short_description,
                "longDescription": item.short_description,
                "images": item.images,
            }
            for item in cart_items
        ]
}



async def checkout(db: AsyncSession, user_id: str):
    # Find the user's cart
    result = await db.execute(select(Cart).filter(Cart.user_id == user_id))
    cart = result.scalars().first()
    if not cart:
        raise ValueError("Cart not found for the user.")

    # Retrieve all items in the cart
    result = await db.execute(
        select(CartItem).filter(CartItem.cart_id == cart.id).options(selectinload(CartItem.product))
    )
    cart_items = result.scalars().all()
    if not cart_items:
        raise ValueError("Cart is empty.")

    # Calculate total price
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Proceed with payment logic here
    # ...

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
