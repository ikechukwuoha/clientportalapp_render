from fastapi import APIRouter, Depends, HTTPException, Request, Depends
import httpx
import logging
from fastapi import HTTPException
from dotenv import load_dotenv
import os
import hmac
import hashlib
import json







load_dotenv()




PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")



# async def verify_webhook_signature(secret_key: str, request: Request, signature: str):
#     """
#     Verifies the signature of the Paystack webhook using raw payload.
#     """
#     try:
#         # Get the raw request body
#         raw_payload = await request.body
#         logging.info("verify_webhook_signature function called.")
#         logging.info(f"Received Payload: {raw_payload}")
#         logging.info(f"Received Signature: {signature}")

#         # Calculate the HMAC SHA512 signature
#         calculated_signature = hmac.new(
#             key=secret_key.encode('utf-8'),
#             msg=raw_payload,
#             digestmod=hashlib.sha512
#         ).hexdigest()
        
#         logging.info(f"Calculated Signature: {calculated_signature}")

#         # Compare the calculated signature with the received signature
#         if calculated_signature != signature:
#             raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
#         logging.info("Webhook signature verification succeeded.")

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error verifying webhook signature: {str(e)}")






async def verify_webhook_signature(secret_key: str, request: Request, signature: str):
    """
    Verifies the signature of the Paystack webhook using raw payload.
    """
    try:
        # Get the raw request body
        raw_payload = await request.body()
        #logging.info("verify_webhook_signature function called.")
        #logging.info(f"Received Payload: {raw_payload}")
        #logging.info(f"Received Signature: {signature}")

        # Calculate the HMAC SHA512 signature
        calculated_signature = hmac.new(
            key=secret_key.encode('utf-8'),
            msg=raw_payload,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        #logging.info(f"Calculated Signature: {calculated_signature}")

        # Compare the calculated signature with the received signature
        if calculated_signature != signature:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        #logging.info("Webhook signature verification succeeded.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying webhook signature: {str(e)}")




async def verify_paystack_transaction(payment_reference: str):
    """
    Verifies a transaction with Paystack using the payment reference.

    Args:
        payment_reference (str): The payment reference to verify.

    Returns:
        tuple: A tuple containing the Paystack status ("success" or "failed") and response data.

    Raises:
        HTTPException: If the Paystack verification fails or returns unauthorized.
    """
    paystack_url = f"https://api.paystack.co/transaction/verify/{payment_reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(paystack_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                # Check for True or False status instead of 'success' or 'failed'
                if status is True:
                    return "success", data.get("data")
                elif status is False:
                    return "failed", data.get("data")
                else:
                    logging.error(f"Unexpected Paystack response: {data}")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unexpected Paystack status: {status}"
                    )
            elif response.status_code == 401:
                logging.error("Unauthorized: Invalid Payment")
                raise HTTPException(
                    status_code=401, 
                    detail="Unauthorized: Invalid Payment"
                )
            else:
                logging.error(f"Paystack API error: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Paystack API returned an error: {response.text}"
                )
    except httpx.RequestError as e:
        logging.error(f"Error connecting to Paystack: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error connecting to Paystack. Please try again later."
        )  
