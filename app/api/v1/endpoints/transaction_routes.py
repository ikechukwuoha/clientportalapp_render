from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from app.api.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.transaction_schema import TransactionPayload
from app.api.services.transaction_services import store_transaction
from app.api.security.payment_verification import verify_paystack_transaction, verify_webhook_signature
from app.api.models.transactions import UserTransactions
import logging


import os



PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')


secret_key = PAYSTACK_SECRET_KEY


router = APIRouter()

@router.post("/store-transaction", tags=["transaction"])
async def store_transactions_payload(transaction_data: TransactionPayload,
    db: AsyncSession = Depends(get_db)):
    """
    Endpoint to store the transaction payload
    """
    return await store_transaction(transaction_data.model_dump(), db) 





# PAYSTACK WEBHOOK
@router.post("/verify-webhook-payload/webhookpaystack")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Endpoint for receiving Paystack webhook notifications.
    """
    try:
        # Restrict Access to Webhook Endpoint (IP check)
        # client_ip = request.client.host
        # if client_ip not in ALLOWED_PAYSTACK_IPS:
        #     raise HTTPException(status_code=403, detail="Forbidden: Invalid IP")

        # Extract the Paystack signature from the headers
        paystack_signature = request.headers.get("x-paystack-signature")
        if not paystack_signature:
            raise HTTPException(status_code=400, detail="Missing Paystack signature")
        
        # Parse the request body (JSON data from Paystack)
        payload = await request.json()
        logging.info(f"Paystack Webhook Payload1111111111111111111111111111111111111111111: {payload}")
        
        #Verify the webhook signature
        

        #Extract event and transaction data
        event = payload.get('event')
        transaction_data = payload.get('data')

        # Log the event and transaction data for better tracking
        logging.info(f"Paystack Webhook Event: {event}")
        logging.info(f"Paystack Transaction Data: {transaction_data}")

        if not event or not transaction_data:
            raise HTTPException(status_code=400, detail="Invalid payload received from Paystack")

        # Verify the transaction via Paystack API
        payment_reference = transaction_data.get("reference")
        paystack_status, paystack_response = await verify_paystack_transaction(payment_reference)
        
        await verify_webhook_signature(secret_key, request, paystack_signature)
        

        # Process webhook based on the event type (e.g., payment.success, payment.failed, etc.)
        if event == "charge.success":
            # Update transaction status to success in the database
            transaction_id = transaction_data.get("id")
            logging.info(f"Processing charge.success for transaction_id: {transaction_id}")
            logging.info(f"Comparing The Id from Paystack and database: {transaction_id}")

            transaction = await db.execute(select(UserTransactions).filter(UserTransactions.transaction_id == transaction_id))
            logging.info(f"Transaction Query Result: {transaction}")
            transaction = transaction.scalar_one_or_none()

            if transaction:
                transaction.payment_status = "success"
                transaction.paystack_status = paystack_status
                transaction.paystack_response = paystack_response
                await db.commit()
                logging.info(f"Updated transaction {transaction_id} to success.")
            else:
                raise HTTPException(status_code=404, detail="Transaction not found")

        elif event == "charge.failed":
            # Handle payment failure (e.g., update the payment status to failed)
            transaction_id = transaction_data.get("id")
            logging.info(f"Processing charge.success for transaction_id: {transaction_id}")

            transaction = await db.execute(select(UserTransactions).filter(UserTransactions.transaction_id == transaction_id))
            transaction = transaction.scalar_one_or_none()

            if transaction is None:
                logging.error(f"Transaction not found for transaction_id: {transaction_id}")
                raise HTTPException(status_code=404, detail="Transaction not found")

            # Update transaction status
            transaction.payment_status = "failed"
            transaction.paystack_status = paystack_status
            transaction.paystack_response = paystack_response
            await db.commit()
            logging.info(f"Updated transaction {transaction_id} to success.")

    except Exception as e:
        logging.error(f"Error handling Paystack webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing Paystack webhook")




















# # PAYSTACK WEBHOOK
# @router.post("/paystack/webhook")
# async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
#     """
#     Endpoint for receiving Paystack webhook notifications.
#     """
#     try:
#         # Extract the Paystack signature from the headers
#         paystack_signature = request.headers.get("x-paystack-signature")
#         if not paystack_signature:
#             raise HTTPException(status_code=400, detail="Missing Paystack signature")
        
#         # Parse the request body (JSON data from Paystack)
#         payload = await request.json()
#         logging.info(f"Paystack Webhook Payload: {payload}")
        
#         # Verify the webhook signature
#         await verify_webhook_signature(secret_key, payload, paystack_signature)

#         # Extract event and transaction data
#         event = payload.get('event')
#         transaction_data = payload.get('data')

#         # Log the event and transaction data for better tracking
#         logging.info(f"Paystack Webhook Event: {event}")
#         logging.info(f"Paystack Transaction Data: {transaction_data}")

#         if not event or not transaction_data:
#             raise HTTPException(status_code=400, detail="Invalid payload received from Paystack")

#         # Verify the transaction via Paystack API
#         payment_reference = transaction_data.get("reference")
#         paystack_status, paystack_response = await verify_paystack_transaction(payment_reference)

#         # Process webhook based on the event type (e.g., payment.success, payment.failed, etc.)
#         if event == "charge.success":
#             # Update transaction status to success in the database
#             transaction_id = str(transaction_data.get("id"))
#             logging.info(f"Processing charge.success for transaction_id: {transaction_id}")
#             logging.info(f"Comparing The Id from Paystack and database22222222222222222222222222222 transaction_id: {transaction_id}")

#             transaction = await db.execute(select(UserTransactions).filter(UserTransactions.transaction_id == transaction_id))
#             logging.info(f"Comparing The Id from Paystack and database11111111111111111111111111111 transaction_id: {transaction_id}")
#             logging.info(f"Transaction Query Result: {transaction}")
            
#             transaction = transaction.scalar_one_or_none()

#             if transaction:
#                 transaction.payment_status = "success"
#                 transaction.paystack_status = paystack_status
#                 transaction.paystack_response = paystack_response
#                 await db.commit()
#                 logging.info(f"Updated transaction {transaction_id} to success.")
#             else:
#                 raise HTTPException(status_code=404, detail="Transaction not found")

#         elif event == "charge.failed":
#             # Handle payment failure (e.g., update the payment status to failed)
#             transaction_id = str(transaction_data.get("id"))  # Convert to string
#             logging.info(f"Processing charge.failed for transaction_id: {transaction_id}")

#             transaction = await db.execute(select(UserTransactions).filter(UserTransactions.transaction_id == transaction_id))
#             logging.info(f"Transaction Query Result: {transaction}")
#             transaction = transaction.scalar_one_or_none()

#             if transaction:
#                 transaction.payment_status = "failed"
#                 transaction.paystack_status = paystack_status
#                 transaction.paystack_response = paystack_response
#                 await db.commit()
#                 logging.info(f"Updated transaction {transaction_id} to failed.")
#             else:
#                 raise HTTPException(status_code=404, detail="Transaction not found")
        
#         # Add handling for other Paystack events like refund, chargeback, etc.
#         # if event == "refund.success":
#         #     # Handle refund event

#         return {"status": "success", "message": "Webhook handled successfully."}

#     except Exception as e:
#         logging.error(f"Error handling Paystack webhook: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error processing Paystack webhook")