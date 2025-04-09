import uuid
import logging

from sqlalchemy import select
from app.api.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models.site_data import SiteData
from app.api.models.transactions import UserTransactions
from fastapi import APIRouter, HTTPException, Depends
from app.api.models.user_model import User
from app.api.security.payment_verification import verify_paystack_transaction
# from app.api.utils.fr_utils import update_frappe_doctype  # Utility to update Frappe ER
import httpx

from app.api.utils.frappe_utils import create_frappe_site, store_site_data

from sqlalchemy.exc import NoResultFound

from datetime import datetime, timedelta


import json
from typing import Dict, Any

from app.api.utils.json_encoder import CustomJSONEncoder
from app.api.utils.normalize_site_name import normalize_site_name, validate_site_name


    

async def store_transaction(transaction_data: dict, db: AsyncSession = Depends(get_db)):
    """
    Store a transaction from the frontend, validate it with Paystack, and store the response in the database.
    """
    # Create a safe copy of transaction data for logging
    safe_data = {
        k: str(v) if isinstance(v, (datetime, uuid.UUID)) else v 
        for k, v in transaction_data.items()
    }
    logging.info(f"Received transaction data: {json.dumps(safe_data, cls=CustomJSONEncoder)}")
    
    try:
        # Extract all fields from transaction data with type validation
        def get_field(field_name: str, required: bool = True, field_type: type = str) -> Any:
            value = transaction_data.get(field_name)
            if value is None and required:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field_name}"
                )
            if value is not None and not isinstance(value, field_type) and field_type != datetime:
                try:
                    value = field_type(value)
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid type for {field_name}. Expected {field_type.__name__}"
                    )
            return value

        # Extract fields with type validation
        user_id = get_field("user_id", field_type=str)  # Will be converted to UUID later
        payment_reference = get_field("payment_reference")
        plan = get_field("plan")
        first_name = get_field("first_name")
        last_name = get_field("last_name")
        email = get_field("email")
        payment_status = get_field("payment_status")
        phone = get_field("phone")
        country = get_field("country")
        company_name = get_field("company_name")
        organization = get_field("organization")
        original_site_name = get_field("site_name")
        
        # Normalize the site name
        site_name = normalize_site_name(original_site_name)
        
        # Validate the normalized site name
        if not validate_site_name(site_name):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid site name after normalization: {site_name}"
            )
            
        quantity = get_field("quantity", field_type=int)
        amount = get_field("amount", field_type=float)
        # We'll ignore valid_from and valid_upto from frontend
        # These variables are just here for backward compatibility with frontend
        _ = get_field("valid_from", required=False)
        _ = get_field("valid_upto", required=False)
        training_and_setup = get_field("training_and_setup", field_type=bool)
        transaction_id = get_field("transaction_id", field_type=int)
        message = get_field("message")

        # Calculate valid_from and valid_upto based on current time and plan
        valid_from = datetime.now()
        
        # Calculate valid_upto based on the plan
        if plan.lower() in ["standard", "custom"]:
            # One year from now
            valid_upto = valid_from + timedelta(days=365)
        elif plan.lower() == "free":
            # 14 days (two weeks) from now
            valid_upto = valid_from + timedelta(days=14)
        else:
            # Default to one year for any other plan
            valid_upto = valid_from + timedelta(days=365)
            logging.warning(f"Unknown plan type: {plan}, defaulting to 1 year validity")

        # Convert user_id to UUID with error handling
        try:
            user_id = uuid.UUID(str(user_id))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid UUID format for user_id"
            )

        # Verify user exists
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Verify payment with Paystack
        paystack_status, paystack_response = await verify_paystack_transaction(payment_reference)
        logging.info(f"Paystack status: {paystack_status}")
        logging.info(f"Paystack response: {paystack_response}")
        
        if paystack_status not in ["success", "failed"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid Paystack transaction status. Please verify your payment reference."
            )

        # If payment failed, don't proceed with site creation
        if paystack_status == "failed":
            raise HTTPException(
                status_code=400,
                detail="Payment verification failed"
            )

        # Create transaction record
        users_transactions = UserTransactions(
            user_id=user_id,
            plan=plan,
            payment_status=payment_status,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            country=country,
            company_name=company_name,
            organization=organization,
            site_name=site_name,  # Store normalized site name
            quantity=quantity,
            amount=amount,
            valid_from=valid_from,
            valid_upto=valid_upto,
            training_and_setup=training_and_setup,
            payment_reference=payment_reference,
            transaction_id=transaction_id,
            message=message,
            paystack_status=paystack_status,
            paystack_response=json.dumps(paystack_response, cls=CustomJSONEncoder),
        )

        # Save transaction to database with safe serialization
        db.add(users_transactions)
        await db.commit()
        await db.refresh(users_transactions)
        
        site_creation_response = None
        
        if paystack_status == "success":
            try:
                logging.info("Attempting to create Frappe site...")
                # Create Frappe site with normalized site name (without storing site data in Frappe)
                site_creation_response = await create_frappe_site(
                    site_name=site_name, 
                    plan=plan,
                    quantity=quantity
                )
                logging.info(f"Site creation response: {site_creation_response}")
                
                # Update transaction with site creation status
                users_transactions.site_creation_status = "initiated"
                if site_creation_response and "job_id" in site_creation_response:
                    users_transactions.site_creation_job_id = site_creation_response.get("job_id")
                
                await db.commit()
                
                logging.info(f"Site creation initiated successfully for {site_name}")
                
            except Exception as e:
                error_msg = f"Error in site creation process: {str(e)}"
                logging.error(error_msg)
                users_transactions.site_creation_status = "failed"
                users_transactions.site_creation_error = error_msg
                await db.commit()
                # We don't raise an exception here as the payment was successful

        # Return success response with all relevant data
        return {
            "message": "Transaction stored successfully",
            "transaction": {
                "id": str(users_transactions.id),
                "user_id": str(users_transactions.user_id),
                "plan": users_transactions.plan,
                "payment_status": users_transactions.payment_status,
                "paystack_status": paystack_status,
                "site_name": users_transactions.site_name,
                "original_site_name": original_site_name,  # Include the original site name in response
                "site_creation_status": users_transactions.site_creation_status,
                "site_creation_job_id": getattr(users_transactions, 'site_creation_job_id', None),
                "valid_from": valid_from.isoformat(),
                "valid_upto": valid_upto.isoformat()
            },
            "site_creation": site_creation_response if site_creation_response else None
        }

    except HTTPException as e:
        logging.error(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"Unhandled error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing transaction: {str(e)}")    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# async def store_transaction(transaction_data: dict, db: AsyncSession = Depends(get_db)):
#     """
#     Store a transaction from the frontend, validate it with Paystack, and store the response in the database.
#     """
#     # Create a safe copy of transaction data for logging
#     safe_data = {
#         k: str(v) if isinstance(v, (datetime, uuid.UUID)) else v 
#         for k, v in transaction_data.items()
#     }
#     logging.info(f"Received transaction data: {json.dumps(safe_data, cls=CustomJSONEncoder)}")
    
#     try:
#         # Extract all fields from transaction data with type validation
#         def get_field(field_name: str, required: bool = True, field_type: type = str) -> Any:
#             value = transaction_data.get(field_name)
#             if value is None and required:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Missing required field: {field_name}"
#                 )
#             if value is not None and not isinstance(value, field_type) and field_type != datetime:
#                 try:
#                     value = field_type(value)
#                 except (ValueError, TypeError):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"Invalid type for {field_name}. Expected {field_type.__name__}"
#                     )
#             return value

#         # Extract fields with type validation
#         user_id = get_field("user_id", field_type=str)  # Will be converted to UUID later
#         payment_reference = get_field("payment_reference")
#         plan = get_field("plan")
#         first_name = get_field("first_name")
#         last_name = get_field("last_name")
#         email = get_field("email")
#         payment_status = get_field("payment_status")
#         phone = get_field("phone")
#         country = get_field("country")
#         company_name = get_field("company_name")
#         organization = get_field("organization")
#         original_site_name = get_field("site_name")
        
#         # Normalize the site name
#         site_name = normalize_site_name(original_site_name)
        
#         # Validate the normalized site name
#         if not validate_site_name(site_name.split(".")[0]):
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid site name after normalization: {site_name}"
#             )
            
#         quantity = get_field("quantity", field_type=int)
#         amount = get_field("amount", field_type=float)
#         valid_from_str = get_field("valid_from")
#         valid_upto_str = get_field("valid_upto")
#         training_and_setup = get_field("training_and_setup", field_type=bool)
#         transaction_id = get_field("transaction_id", field_type=int)
#         message = get_field("message")

#         # Parse dates with error handling
#         try:
#             valid_from = datetime.strptime(valid_from_str, "%Y-%m-%d")
#             valid_upto = datetime.strptime(valid_upto_str, "%Y-%m-%d")
#         except ValueError as e:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid date format. Dates should be in YYYY-MM-DD format: {str(e)}"
#             )

#         # Convert user_id to UUID with error handling
#         try:
#             user_id = uuid.UUID(str(user_id))
#         except ValueError:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid UUID format for user_id"
#             )

#         # Verify user exists
#         result = await db.execute(select(User).filter(User.id == user_id))
#         user = result.scalar_one_or_none()
#         if not user:
#             raise HTTPException(
#                 status_code=404,
#                 detail="User not found"
#             )

#         # Verify payment with Paystack
#         paystack_status, paystack_response = await verify_paystack_transaction(payment_reference)
#         logging.info(f"Paystack status: {paystack_status}")
#         logging.info(f"Paystack response: {paystack_response}")
        
#         if paystack_status not in ["success", "failed"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid Paystack transaction status. Please verify your payment reference."
#             )

#         # If payment failed, don't proceed with site creation
#         if paystack_status == "failed":
#             raise HTTPException(
#                 status_code=400,
#                 detail="Payment verification failed"
#             )

#         # Create transaction record
#         users_transactions = UserTransactions(
#             user_id=user_id,
#             plan=plan,
#             payment_status=payment_status,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             phone=phone,
#             country=country,
#             company_name=company_name,
#             organization=organization,
#             site_name=site_name,  # Store normalized site name
#             quantity=quantity,
#             amount=amount,
#             valid_from=valid_from,
#             valid_upto=valid_upto,
#             training_and_setup=training_and_setup,
#             payment_reference=payment_reference,
#             transaction_id=transaction_id,
#             message=message,
#             paystack_status=paystack_status,
#             paystack_response=json.dumps(paystack_response, cls=CustomJSONEncoder),
#         )

#         # Save transaction to database with safe serialization
#         db.add(users_transactions)
#         await db.commit()
#         await db.refresh(users_transactions)
        
#         site_creation_response = None
        
#         if paystack_status == "success":
#             try:
#                 logging.info("Attempting to create Frappe site...")
#                 # Create Frappe site with normalized site name (without storing site data in Frappe)
#                 site_creation_response = await create_frappe_site(
#                     site_name=site_name, 
#                     plan=plan,
#                     quantity=quantity
#                 )
#                 logging.info(f"Site creation response: {site_creation_response}")
                
#                 # Update transaction with site creation status
#                 users_transactions.site_creation_status = "initiated"
#                 if site_creation_response and "job_id" in site_creation_response:
#                     users_transactions.site_creation_job_id = site_creation_response.get("job_id")
                
#                 await db.commit()
                
#                 logging.info(f"Site creation initiated successfully for {site_name}")
                
#             except Exception as e:
#                 error_msg = f"Error in site creation process: {str(e)}"
#                 logging.error(error_msg)
#                 users_transactions.site_creation_status = "failed"
#                 users_transactions.site_creation_error = error_msg
#                 await db.commit()
#                 # We don't raise an exception here as the payment was successful

#         # Return success response with all relevant data
#         return {
#             "message": "Transaction stored successfully",
#             "transaction": {
#                 "id": str(users_transactions.id),
#                 "user_id": str(users_transactions.user_id),
#                 "plan": users_transactions.plan,
#                 "payment_status": users_transactions.payment_status,
#                 "paystack_status": paystack_status,
#                 "site_name": users_transactions.site_name,
#                 "original_site_name": original_site_name,  # Include the original site name in response
#                 "site_creation_status": users_transactions.site_creation_status,
#                 "site_creation_job_id": getattr(users_transactions, 'site_creation_job_id', None)
#             },
#             "site_creation": site_creation_response if site_creation_response else None
#         }

#     except HTTPException as e:
#         logging.error(f"HTTPException: {e.detail}")
#         raise e
#     except Exception as e:
#         logging.error(f"Unhandled error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error storing transaction: {str(e)}")






async def get_transactions_by_user_id(user_id: str, db: AsyncSession):
    try:
        # Fetch transactions with corresponding site data in one query
        query = (
            select(UserTransactions, SiteData.active_sites)
            .join(SiteData, UserTransactions.site_name == SiteData.site_name, isouter=True)
            .filter(UserTransactions.user_id == user_id)
        )
        result = await db.execute(query)
        transactions_with_sites = result.all()
        
        if not transactions_with_sites:
            raise HTTPException(status_code=404, detail="No transactions found for this user")

        return transactions_with_sites
    except NoResultFound:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")





async def get_transaction_by_id(transaction_id: str, db: AsyncSession) -> tuple:
    """
    Fetch a single transaction with corresponding site data by transaction_id.
    """
    try:
        query = (
            select(UserTransactions, SiteData.active_sites)
            .join(SiteData, UserTransactions.site_name == SiteData.site_name, isouter=True)
            .filter(UserTransactions.id == transaction_id)
        )
        result = await db.execute(query)
        transaction_with_site = result.first()
        
        if not transaction_with_site:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction with ID {transaction_id} not found"
            )

        return transaction_with_site
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching transaction: {str(e)}"
        )
    
    


# async def store_transaction(transaction_data: dict, db: AsyncSession = Depends(get_db)):
#     """
#     Store a transaction from the frontend, validate it with Paystack, and store the response in the database.
#     """
#     # Create a safe copy of transaction data for logging
#     safe_data = {
#         k: str(v) if isinstance(v, (datetime, uuid.UUID)) else v 
#         for k, v in transaction_data.items()
#     }
#     logging.info(f"Received transaction data: {json.dumps(safe_data, cls=CustomJSONEncoder)}")
#     print("This is the Transaxtion Data ......................................................................................................................................", transaction_data)
    
#     try:
#         # Extract all fields from transaction data with type validation
#         def get_field(field_name: str, required: bool = True, field_type: type = str) -> Any:
#             value = transaction_data.get(field_name)
#             if value is None and required:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Missing required field: {field_name}"
#                 )
#             if value is not None and not isinstance(value, field_type) and field_type != datetime:
#                 try:
#                     value = field_type(value)
#                 except (ValueError, TypeError):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"Invalid type for {field_name}. Expected {field_type.__name__}"
#                     )
#             return value

#         # Extract fields with type validation
#         user_id = get_field("user_id", field_type=str)  # Will be converted to UUID later
#         payment_reference = get_field("payment_reference")
#         plan = get_field("plan")
#         first_name = get_field("first_name")
#         last_name = get_field("last_name")
#         email = get_field("email")
#         payment_status = get_field("payment_status")
#         phone = get_field("phone")
#         country = get_field("country")
#         company_name = get_field("company_name")
#         organization = get_field("organization")
#         original_site_name = get_field("site_name")
        
#         # Normalize the site name
#         site_name = normalize_site_name(original_site_name)
        
#         # Validate the normalized site name
#         if not validate_site_name(site_name.split(".")[0]):
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid site name after normalization: {site_name}"
#             )
            
#         quantity = get_field("quantity", field_type=int)
#         amount = get_field("amount", field_type=float)
#         valid_from_str = get_field("valid_from")
#         valid_upto_str = get_field("valid_upto")
#         training_and_setup = get_field("training_and_setup", field_type=bool)
#         transaction_id = get_field("transaction_id", field_type=int)
#         message = get_field("message")

#         # Parse dates with error handling
#         try:
#             valid_from = datetime.strptime(valid_from_str, "%Y-%m-%d")
#             valid_upto = datetime.strptime(valid_upto_str, "%Y-%m-%d")
#         except ValueError as e:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid date format. Dates should be in YYYY-MM-DD format: {str(e)}"
#             )

#         # Convert user_id to UUID with error handling
#         try:
#             user_id = uuid.UUID(str(user_id))
#         except ValueError:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid UUID format for user_id"
#             )

#         # Verify user exists
#         result = await db.execute(select(User).filter(User.id == user_id))
#         user = result.scalar_one_or_none()
#         if not user:
#             raise HTTPException(
#                 status_code=404,
#                 detail="User not found"
#             )
        
#         print(",3,3,,3,3,3,3,3,3m33m3m3m3m3m3m3m3m3m3m3m333333333333333333333333333333m3m3m3m3m3m3m3", payment_reference)

#         # Verify payment with Paystack
#         paystack_status, paystack_response = await verify_paystack_transaction(payment_reference)
#         if paystack_status not in ["success", "failed"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid Paystack transaction status. Please verify your payment reference."
#             )

#         # If payment failed, don't proceed with site creation
#         if paystack_status == "failed":
#             raise HTTPException(
#                 status_code=400,
#                 detail="Payment verification failed"
#             )

#         # Create transaction record
#         users_transactions = UserTransactions(
#             user_id=user_id,
#             plan=plan,
#             payment_status=payment_status,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             phone=phone,
#             country=country,
#             company_name=company_name,
#             organization=organization,
#             site_name=site_name,  # Store normalized site name
#             quantity=quantity,
#             amount=amount,
#             valid_from=valid_from,
#             valid_upto=valid_upto,
#             training_and_setup=training_and_setup,
#             payment_reference=payment_reference,
#             transaction_id=transaction_id,
#             message=message,
#             paystack_status=paystack_status,
#             paystack_response=json.dumps(paystack_response, cls=CustomJSONEncoder),
#         )

#         # Save transaction to database with safe serialization
#         db.add(users_transactions)
#         await db.commit()
#         await db.refresh(users_transactions)
        
#         site_creation_response = None
#         frappe_response = None
        
#         if paystack_status == "success":
#             try:
#                 # Create Frappe site with normalized site name
#                 site_creation_response = await create_frappe_site(site_name=site_name, plan=plan)
                
#                 # Update transaction with site creation status
#                 users_transactions.site_creation_status = "initiated"
#                 users_transactions.site_creation_job_id = site_creation_response.get("job_id")
                
#                 # Store additional site data in Frappe with normalized site name
#                 frappe_data = {
#                     "first_name": first_name,
#                     "last_name": last_name,
#                     "email": email,
#                     "phone": phone,
#                     "country": country,
#                     "company_name": company_name,
#                     "organization": organization,
#                     "site_name": site_name,  # Use normalized site name
#                     "valid_from": valid_from.strftime("%Y-%m-%d"),
#                     "valid_upto": valid_upto.strftime("%Y-%m-%d"),
#                     "status": payment_status,
#                     "product": plan
#                 }
                
#                 frappe_response = await store_site_data(frappe_data)
                
#                 # Update final status
#                 users_transactions.site_creation_status = "success"
#                 await db.commit()
                
#                 logging.info(f"Site creation initiated successfully for {site_name}")
                
#             except Exception as e:
#                 error_msg = f"Error in site creation process: {str(e)}"
#                 logging.error(error_msg)
#                 users_transactions.site_creation_status = "failed"
#                 users_transactions.site_creation_error = error_msg
#                 await db.commit()
#                 # We don't raise an exception here as the payment was successful

#         # Return success response with all relevant data
#         return {
#             "message": "Transaction stored successfully",
#             "transaction": {
#                 "id": str(users_transactions.id),
#                 "user_id": str(users_transactions.user_id),
#                 "plan": users_transactions.plan,
#                 "payment_status": users_transactions.payment_status,
#                 "paystack_status": paystack_status,
#                 "site_name": users_transactions.site_name,
#                 "original_site_name": original_site_name,  # Include the original site name in response
#                 "site_creation_status": users_transactions.site_creation_status,
#                 "site_creation_job_id": getattr(users_transactions, 'site_creation_job_id', None)
#             },
#             "site_creation": site_creation_response if site_creation_response else None,
#             "frappe_update": frappe_response if frappe_response else None
#         }

#     except HTTPException as e:
#         logging.error(f"HTTPException: {e.detail}")
#         raise e
#     except Exception as e:
#         logging.error(f"Unhandled error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error storing transaction: {str(e)}")




# async def store_transaction(transaction_data: dict, db: AsyncSession = Depends(get_db)):
#     """
#     Store a transaction from the frontend, validate it with Paystack, and store the response in the database.
#     """
#     # Create a safe copy of transaction data for logging
#     safe_data = {
#         k: str(v) if isinstance(v, (datetime, uuid.UUID)) else v 
#         for k, v in transaction_data.items()
#     }
#     logging.info(f"Received transaction data: {json.dumps(safe_data, cls=CustomJSONEncoder)}")
#     print("This is the Transaxtion Data ......................................................................................................................................", transaction_data)
    
#     try:
#         # Extract all fields from transaction data with type validation
#         def get_field(field_name: str, required: bool = True, field_type: type = str) -> Any:
#             value = transaction_data.get(field_name)
#             if value is None and required:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Missing required field: {field_name}"
#                 )
#             if value is not None and not isinstance(value, field_type) and field_type != datetime:
#                 try:
#                     value = field_type(value)
#                 except (ValueError, TypeError):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"Invalid type for {field_name}. Expected {field_type.__name__}"
#                     )
#             return value

#         # Extract fields with type validation
#         user_id = get_field("user_id", field_type=str)  # Will be converted to UUID later
#         payment_reference = get_field("payment_reference")
#         plan = get_field("plan")
#         first_name = get_field("first_name")
#         last_name = get_field("last_name")
#         email = get_field("email")
#         payment_status = get_field("payment_status")
#         phone = get_field("phone")
#         country = get_field("country")
#         company_name = get_field("company_name")
#         organization = get_field("organization")
#         site_name = get_field("site_name")
#         quantity = get_field("quantity", field_type=int)
#         amount = get_field("amount", field_type=float)
#         valid_from_str = get_field("valid_from")
#         valid_upto_str = get_field("valid_upto")
#         training_and_setup = get_field("training_and_setup", field_type=bool)
#         transaction_id = get_field("transaction_id", field_type=int)
#         message = get_field("message")

#         # Parse dates with error handling
#         try:
#             valid_from = datetime.strptime(valid_from_str, "%Y-%m-%d")
#             valid_upto = datetime.strptime(valid_upto_str, "%Y-%m-%d")
#         except ValueError as e:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid date format. Dates should be in YYYY-MM-DD format: {str(e)}"
#             )

#         # Convert user_id to UUID with error handling
#         try:
#             user_id = uuid.UUID(str(user_id))
#         except ValueError:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid UUID format for user_id"
#             )

#         # Verify user exists
#         result = await db.execute(select(User).filter(User.id == user_id))
#         user = result.scalar_one_or_none()
#         if not user:
#             raise HTTPException(
#                 status_code=404,
#                 detail="User not found"
#             )
        
#         print(",3,3,,3,3,3,3,3,3m33m3m3m3m3m3m3m3m3m3m3m333333333333333333333333333333m3m3m3m3m3m3m3", payment_reference)

#         # Verify payment with Paystack
#         paystack_status, paystack_response = await verify_paystack_transaction(payment_reference)
#         if paystack_status not in ["success", "failed"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid Paystack transaction status. Please verify your payment reference."
#             )

#         # If payment failed, don't proceed with site creation
#         if paystack_status == "failed":
#             raise HTTPException(
#                 status_code=400,
#                 detail="Payment verification failed"
#             )

#         # Create transaction record
#         users_transactions = UserTransactions(
#             user_id=user_id,
#             plan=plan,
#             payment_status=payment_status,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             phone=phone,
#             country=country,
#             company_name=company_name,
#             organization=organization,
#             site_name=site_name,
#             quantity=quantity,
#             amount=amount,
#             valid_from=valid_from,
#             valid_upto=valid_upto,
#             training_and_setup=training_and_setup,
#             payment_reference=payment_reference,
#             transaction_id=transaction_id,
#             message=message,
#             paystack_status=paystack_status,
#             paystack_response=json.dumps(paystack_response, cls=CustomJSONEncoder),
#         )

#         # Save transaction to database with safe serialization
#         db.add(users_transactions)
#         await db.commit()
#         await db.refresh(users_transactions)
        
#         site_creation_response = None
#         frappe_response = None
        
#         if paystack_status == "success":
#             try:
#                 # Create Frappe site
#                 site_creation_response = await create_frappe_site(site_name=site_name)
                
#                 # Update transaction with site creation status
#                 users_transactions.site_creation_status = "initiated"
#                 users_transactions.site_creation_job_id = site_creation_response.get("job_id")
                
#                 # Store additional site data in Frappe
#                 frappe_data = {
#                     "first_name": first_name,
#                     "last_name": last_name,
#                     "email": email,
#                     "phone": phone,
#                     "country": country,
#                     "company_name": company_name,
#                     "organization": organization,
#                     "site_name": site_name,
#                     "valid_from": valid_from.strftime("%Y-%m-%d"),
#                     "valid_upto": valid_upto.strftime("%Y-%m-%d"),
#                     "status": payment_status,
#                     "product": plan
#                 }
                
#                 frappe_response = await store_site_data(frappe_data)
                
#                 # Update final status
#                 users_transactions.site_creation_status = "success"
#                 await db.commit()
                
#                 logging.info(f"Site creation initiated successfully for {site_name}")
                
#             except Exception as e:
#                 error_msg = f"Error in site creation process: {str(e)}"
#                 logging.error(error_msg)
#                 users_transactions.site_creation_status = "failed"
#                 users_transactions.site_creation_error = error_msg
#                 await db.commit()
#                 # We don't raise an exception here as the payment was successful

#         # Return success response with all relevant data
#         return {
#             "message": "Transaction stored successfully",
#             "transaction": {
#                 "id": str(users_transactions.id),
#                 "user_id": str(users_transactions.user_id),
#                 "plan": users_transactions.plan,
#                 "payment_status": users_transactions.payment_status,
#                 "paystack_status": paystack_status,
#                 "site_name": users_transactions.site_name,
#                 "site_creation_status": users_transactions.site_creation_status,
#                 "site_creation_job_id": getattr(users_transactions, 'site_creation_job_id', None)
#             },
#             "site_creation": site_creation_response if site_creation_response else None,
#             "frappe_update": frappe_response if frappe_response else None
#         }

#     except HTTPException as e:
#         logging.error(f"HTTPException: {e.detail}")
#         raise e
#     except Exception as e:
#         logging.error(f"Unhandled error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error storing transaction: {str(e)}")





# async def get_transactions_by_user_id(user_id: str, db: AsyncSession):
#     try:
#         # Fetch transactions with corresponding site data in one query
#         query = (
#             select(UserTransactions, SiteData.active_sites)
#             .join(SiteData, UserTransactions.site_name == SiteData.site_name, isouter=True)
#             .filter(UserTransactions.user_id == user_id)
#         )
#         result = await db.execute(query)
#         transactions_with_sites = result.all()
        
#         if not transactions_with_sites:
#             raise HTTPException(status_code=404, detail="No transactions found for this user")

#         return transactions_with_sites
#     except NoResultFound:
#         raise HTTPException(status_code=404, detail="User not found")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")






# async def get_transactions_by_user_id(user_id: str, db: AsyncSession):
#     try:
#         # Fetch all transactions for the given user_id
#         result = await db.execute(select(UserTransactions).filter(UserTransactions.user_id == user_id))
#         transactions = result.scalars().all()
        
#         if not transactions:
#             raise HTTPException(status_code=404, detail="No transactions found for this user")

#         return transactions
#     except NoResultFound:
#         raise HTTPException(status_code=404, detail="User not found")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")








# async def store_transaction(transaction_data: dict, db: AsyncSession = Depends(get_db)):
#     """
#     Store a transaction from the frontend, validate it with Paystack, and store the response in the database.
#     """
#     logging.info(f"Received transaction data: {transaction_data}")
#     print("Transaction Data From Client", transaction_data)
#     try:
#         # Extract transaction fields
#         user_id = transaction_data.get("user_id")
#         payment_reference = transaction_data.get("payment_reference")
#         plan = transaction_data.get("plan")
#         first_name = transaction_data.get("first_name")
#         last_name = transaction_data.get("last_name")
#         email = transaction_data.get("email")
#         payment_status = transaction_data.get("payment_status")
#         phone = transaction_data.get("phone")
#         country = transaction_data.get("country")
#         company_name = transaction_data.get("company_name")
#         organization = transaction_data.get("organization")
#         site_name = transaction_data.get("site_name")
#         quantity = transaction_data.get("quantity")
#         amount = transaction_data.get("amount")
#         valid_from = transaction_data.get("valid_from")
#         valid_upto = transaction_data.get("valid_upto")
#         training_and_setup = transaction_data.get("training_and_setup")
#         transaction_id = transaction_data.get("transaction_id")
#         message = transaction_data.get("message")

#         #logging.info(f"Transaction data: {transaction_data}")

#         # Check for missing required fields individually and raise detailed errors
#         required_fields = {
#             "user_id": user_id,
#             "plan": plan,
#             "first_name": first_name,
#             "last_name": last_name,
#             "email": email,
#             "phone": phone,
#             "country": country,
#             "company_name": company_name,
#             "organization": organization,
#             "site_name": site_name,
#             "quantity": quantity,
#             "amount": amount,
#             "valid_from": valid_from,
#             "valid_upto": valid_upto,
#             "training_and_setup": training_and_setup,
#             "payment_reference": payment_reference,
#             "transaction_id": transaction_id,
#             "message": message,
#             "payment_status": payment_status,
#         }
        
#         valid_from = datetime.strptime(transaction_data.get("valid_from"), "%Y-%m-%d")
#         valid_upto = datetime.strptime(transaction_data.get("valid_upto"), "%Y-%m-%d")
        

#         missing_fields = [field for field, value in required_fields.items() if value is None]
#         if missing_fields:
#             raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing_fields)}")


#         #logging.info(f"Missing fields: {missing_fields}")
        

#         # Convert user_id to UUID if it's not already a UUID
#         try:
#             if not isinstance(user_id, uuid.UUID):
#                 user_id = uuid.UUID(str(user_id))
#         except ValueError:
#             raise HTTPException(status_code=400, detail="Invalid UUID format for user_id")


#         # Fetch the user from the database to check if they exist
#         result = await db.execute(select(User).filter(User.id == user_id))
#         user = result.scalar_one_or_none()
        

#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#        # Verify payment with Paystack using the security module
#         paystack_status, paystack_response = await verify_paystack_transaction(payment_reference)
        
#         try:
#             transaction_id = int(transaction_data.get("transaction_id"))
#         except (ValueError, TypeError):
#             raise HTTPException(
#                 status_code=400, 
#                 detail="transaction_id must be a valid integer"
#             )


#         # Proceed only if Paystack status is "success" or "failed"
#         if paystack_status != "success" and paystack_status != "failed":
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Invalid Paystack transaction status. Please verify your payment reference."
#             )
            
#         # Dynamically trigger Frappe site creation if Paystack status is "success"
#         # if paystack_status == "success":
#         #     admin_password = "admin123456789"
#         #     mysql_password= "Oreoluwa@555"
#         #     frappe_site_creation_response = await create_frappe_site({
#         #         "email": email,
#         #         "site_name": site_name,
#         #         "admin_password": admin_password,
#         #         "mysql_password": mysql_password
#         #     })

#         #     if "status" in frappe_site_creation_response:
#         #         if frappe_site_creation_response["status"] == "failed":
#         #             raise HTTPException(
#         #                 status_code=500,
#         #                 detail=frappe_site_creation_response["message"]
#         #             )
#         #         elif "successfully" in frappe_site_creation_response["message"]:
#         #             # Site creation was successful
#         #             pass
#         #         else:
#         #             raise HTTPException(
#         #                 status_code=500,
#         #                 detail="Unexpected message: " + frappe_site_creation_response["message"]
#         #             )
#         #     else:
#         #         raise HTTPException(
#         #             status_code=500,
#         #             detail="Unknown error occurred during site creation."
#         #         )



#         # Create a new transaction record
#         users_transactions = UserTransactions(
#             user_id=user_id,
#             plan=plan,
#             payment_status=payment_status,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             phone=phone,
#             country=country,
#             company_name=company_name,
#             organization=organization,
#             site_name=site_name,
#             quantity=quantity,
#             amount=amount,
#             valid_from=valid_from,
#             valid_upto=valid_upto,
#             training_and_setup=training_and_setup,
#             payment_reference=payment_reference,
#             transaction_id=transaction_id,
#             message=message,
#             paystack_status=paystack_status,
#             paystack_response=paystack_response,
#         )

#         # Save the transaction to the database
#         db.add(users_transactions)
#         logging.info(f"Attempting to save UserTransactions: {users_transactions}")

#         await db.commit()
#         await db.refresh(users_transactions)
#         #Trigger Frappe update
#         frappe_response = await store_site_data({
#             "first_name": first_name,
#             "last_name": last_name,
#             "email": email,
#             "phone": phone,
#             "country": country,
#             "company_name": company_name,
#             "organization": organization,
#             "site_name": site_name,
#             "valid_from": valid_from,
#             "valid_upto": valid_upto,
#             "status": payment_status,
#             "product": "Hello World!!"
#         })

#         return {
#             "message": "Transaction stored successfully",
#             "transaction": {
#                 "id": users_transactions.id,
#                 "user_id": str(users_transactions.user_id),
#                 "plan": users_transactions.plan,
#                 "payment_status": users_transactions.payment_status,
#                 "paystack_response": users_transactions.paystack_response,
#             },
#             "frappe_update_response": frappe_response
#         }

#     except HTTPException as e:
#         logging.error(f"HTTPException: {e.detail}")
#         raise e
#     except Exception as e:
#         logging.error(f"Unhandled error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error storing transaction")

