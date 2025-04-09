import json
import re
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from app.api.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.transaction_schema import TransactionPayload
from app.api.services.transaction_services import CustomJSONEncoder, get_transaction_by_id, get_transactions_by_user_id, store_transaction
from app.api.security.payment_verification import verify_paystack_transaction, verify_webhook_signature
from app.api.models.transactions import UserTransactions
import logging




import os

from app.api.utils.frappe_utils import store_site_data



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


# @router.post("/webhook/site-creation")
# async def site_creation_webhook(data: dict):
#     # Handle the webhook data
#     print("4444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444", data)
#     return {"status": "received"}



@router.post("/webhook/site-creation")
async def site_creation_webhook(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Handle webhook from site creation service and store site data in Frappe when site is created successfully.
    """
    logging.info(f"Received webhook data: {data}")
    
    try:
        # Check if site creation was successful
        if data.get("status") == "success" and "site_name" in data:
            # Extract site name directly from the data
            site_name = data.get("site_name")
            logging.info(f"Extracted site name: {site_name}")
            
            # Query the transaction to get site data
            try:
                result = await db.execute(
                    select(UserTransactions).filter(UserTransactions.site_name == site_name)
                    .order_by(UserTransactions.created_at.desc())
                    .limit(1)
                )
                transaction = result.scalar_one_or_none()
                
                if not transaction:
                    logging.error(f"No transaction found for site: {site_name}")
                    return {"status": "error", "message": "Transaction not found"}
                
                logging.info(f"Retrieved transaction for site: {site_name}")
            except Exception as db_error:
                logging.error(f"Database query error: {str(db_error)}")
                return {"status": "error", "message": "Database query failed"}
            
            # Prepare site data for Frappe
            site_data = {
                "first_name": transaction.first_name,
                "last_name": transaction.last_name,
                "email": transaction.email,
                "phone": transaction.phone,
                "country": transaction.country,
                "company_name": transaction.company_name,
                "organization": transaction.organization,
                "site_name": transaction.site_name,
                "quantity": transaction.quantity,
                "amount": transaction.amount,
                "training_and_setup": transaction.training_and_setup,
                "payment_reference": transaction.payment_reference,
                "payment_status": transaction.payment_status,
                "valid_from": transaction.valid_from.strftime("%Y-%m-%d"),
                "valid_upto": transaction.valid_upto.strftime("%Y-%m-%d"),
                "status": transaction.payment_status,
                "product": transaction.plan
            }
            
            logging.info(f"Prepared site data for Frappe: {json.dumps(site_data, indent=2)}")
            
            # Store the data in Frappe
            try:
                logging.info(f"Attempting to store site data for {site_name} in Frappe")
                frappe_response = await store_site_data(site_data)
                
                logging.info(f"Frappe response received: {frappe_response}")
                
                # Update transaction with Frappe data storage status
                transaction.frappe_status = "success"
                transaction.frappe_response = json.dumps(frappe_response, cls=CustomJSONEncoder)
                transaction.site_creation_status = "complete"
                
                try:
                    await db.commit()
                    logging.info(f"Transaction updated successfully for {site_name}")
                except Exception as commit_error:
                    logging.error(f"Error committing transaction: {str(commit_error)}")
                    await db.rollback()
                
                logging.info(f"Site data successfully stored in Frappe for {site_name}")
                return {
                    "status": "success", 
                    "message": "Site data stored in Frappe",
                    "frappe_response": frappe_response
                }
                
            except Exception as e:
                error_msg = f"Failed to store site data in Frappe: {str(e)}"
                logging.error(error_msg)
                
                # Update transaction with failure status
                transaction.frappe_status = "failed"
                transaction.frappe_error = error_msg
                
                try:
                    await db.commit()
                    logging.info(f"Transaction updated with failure status for {site_name}")
                except Exception as commit_error:
                    logging.error(f"Error committing failure status: {str(commit_error)}")
                    await db.rollback()
                
                return {"status": "error", "message": error_msg}
        
        # Update site creation status if not successful
        elif data.get("status") == "failed":
            site_name_match = re.search(r'Site ([^\s]+) failed', data.get("message", ""))
            if site_name_match:
                site_name = site_name_match.group(1)
                logging.warning(f"Site creation failed for: {site_name}")
                
                try:
                    result = await db.execute(
                        select(UserTransactions).filter(UserTransactions.site_name == site_name)
                        .order_by(UserTransactions.created_at.desc())
                        .limit(1)
                    )
                    transaction = result.scalar_one_or_none()
                    
                    if transaction:
                        transaction.site_creation_status = "failed"
                        transaction.site_creation_error = data.get("message", "Unknown error")
                        
                        try:
                            await db.commit()
                            logging.info(f"Updated failed site creation status for {site_name}")
                        except Exception as commit_error:
                            logging.error(f"Error committing failed site creation status: {str(commit_error)}")
                            await db.rollback()
                    else:
                        logging.warning(f"No transaction found for failed site: {site_name}")
                
                except Exception as db_error:
                    logging.error(f"Error processing failed site creation: {str(db_error)}")
        
        # Just acknowledge receipt for any other webhook data
        logging.info("Webhook data received but not processed")
        return {"status": "received"}
        
    except Exception as e:
        logging.error(f"Unexpected error processing site creation webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    
    
    
    
    

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






# @router.get("/get-transactions/{user_id}", response_model=List[dict])
# async def fetch_user_transactions(user_id: str, db: AsyncSession = Depends(get_db)):
#     """
#     Fetch all transactions for a specific user based on user_id with active sites.
#     Path parameter:
#     - user_id: The ID of the user whose transactions to fetch
#     """
#     transactions_with_sites = await get_transactions_by_user_id(user_id, db)
#     return [
#         {
#             "id": transaction.id,
#             "user_id": str(transaction.user_id),
#             "plan": transaction.plan,
#             "payment_status": transaction.payment_status,
#             "amount": transaction.amount,
#             "site_name": transaction.site_name,
#             "active_sites": active_sites,
#             "number_of_users": transaction.quantity,
#             "payment_reference": transaction.payment_reference,
#             "transaction_id": transaction.transaction_id,
#             "valid_from": transaction.valid_from,
#             "valid_upto": transaction.valid_upto,
#             "paystack_status": transaction.paystack_status,
#             "created_at": transaction.created_at,
#         }
#         for transaction, active_sites in transactions_with_sites
#     ]

@router.get("/get-transactions/{user_id}", response_model=List[dict])
async def fetch_user_transactions(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch all transactions for a specific user based on user_id with active sites.
    Path parameter:
    - user_id: The ID of the user whose transactions to fetch
    """
    transactions_with_sites = await get_transactions_by_user_id(user_id, db)
    return [
        {
            "id": transaction.id,
            "user_id": str(transaction.user_id),
            "plan": transaction.plan,
            "payment_status": transaction.payment_status,
            "amount": transaction.amount,
            "site_name": transaction.site_name,
            "active_sites": active_sites,
            "number_of_users": transaction.quantity,
            "payment_reference": transaction.payment_reference,
            "transaction_id": transaction.transaction_id,
            "valid_from": transaction.valid_from,
            "valid_upto": transaction.valid_upto,
            "paystack_status": transaction.paystack_status,
            "created_at": transaction.created_at,
        }
        for transaction, active_sites in transactions_with_sites
    ]
    
    
    
    
@router.get("/transactions/{transaction_id}", response_model=Dict)
async def fetch_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch a single transaction by its transaction_id with active sites.
    
    Parameters:
        transaction_id: The unique identifier of the transaction
        db: Database session
    """
    try:
        transaction, active_sites = await get_transaction_by_id(transaction_id, db)
        
        return {
            "message": "Transaction found",
            "transaction": {
                "user_id": str(transaction.user_id),
                "plan": transaction.plan,
                "payment_status": transaction.payment_status,
                "amount": transaction.amount,
                "site_name": transaction.site_name,
                "active_sites": active_sites,
                "number_of_users": transaction.quantity,
                "payment_reference": transaction.payment_reference,
                "transaction_id": transaction.transaction_id,
                "valid_from": transaction.valid_from,
                "valid_upto": transaction.valid_upto,
                "paystack_status": transaction.paystack_status,
                "created_at": transaction.created_at,
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in fetch_transaction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching transaction data"
        )



# @router.get("/get-transactions", response_model=List[dict])  # Response model can be customized
# async def fetch_user_transactions(id: str, db: AsyncSession = Depends(get_db)):
#     """
#     Fetch all transactions for a specific user based on user_id (id as query param).
#     """
#     transactions = await get_transactions_by_user_id(id, db)
#     return [
#         {
#             "id": transaction.id,
#             "user_id": str(transaction.user_id),
#             "plan": transaction.plan,
#             "payment_status": transaction.payment_status,
#             "amount": transaction.amount,
#             "site_name": transaction.site_name,
#             "number_of_users": transaction.quantity,
#             "amount": transaction.amount,
#             "payment_reference": transaction.payment_reference,
#             "transaction_id": transaction.transaction_id,
#             "valid_from": transaction.valid_from,
#             "valid_upto": transaction.valid_upto,
#             "paystack_status": transaction.paystack_status,
#             "created_at": transaction.created_at,
#         }
#         for transaction in transactions
#     ]








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