from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.database.db import get_db
from app.api.schemas.cart_schema import AddItemSchema, UpdateQuantitySchema, CartResponse, CheckoutResponse
from app.api.services.cart_services import (
    add_item_to_cart,
    remove_item_from_cart,
    view_cart,
    checkout,
    update_item_quantity,
)



router = APIRouter()



@router.post("/add-item", response_model=dict, tags=["cart"])
async def add_item(
    data: AddItemSchema, 
    db: AsyncSession = Depends(get_db)
):
    """
    Add an item to the cart.
    """
    try:
        return await add_item_to_cart(db, data.user_id, data.product_id, data.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/remove-item", response_model=dict, tags=["cart"])
async def remove_item(
    user_id: str, 
    product_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an item from the cart.
    """
    try:
        return await remove_item_from_cart(db, user_id, product_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/view-cart", response_model=CartResponse, tags=["cart"])
async def view_cart_route(
    user_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    View items in the cart.
    """
    try:
        return await view_cart(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/checkout", response_model=CheckoutResponse, tags=["cart"])
async def checkout_route(
    user_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Checkout and clear the cart.
    """
    try:
        return await checkout(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/update-quantity", response_model=dict, tags=["cart"])
async def update_quantity(
    data: UpdateQuantitySchema, 
    db: AsyncSession = Depends(get_db)
):
    """
    Update the quantity of an item in the cart.
    """
    try:
        return await update_item_quantity(db, data.user_id, data.product_id, data.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
