from app.api.models.cart import Cart 




async def create_cart(db, user_id: str):
    """
    Create a cart for the given user ID.
    """
    cart = Cart(user_id=user_id)
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    return cart
