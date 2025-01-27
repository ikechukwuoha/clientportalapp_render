import uuid
import logging

from sqlalchemy import select
from app.api.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models.transactions import UserTransactions
from fastapi import APIRouter, HTTPException, Depends
from app.api.models.user_model import User
from app.api.security.payment_verification import verify_paystack_transaction
# from app.api.utils.fr_utils import update_frappe_doctype  # Utility to update Frappe ER
import httpx

from app.api.utils.frappe_utils import create_frappe_site, store_site_data




async def store_transaction(transaction_data: dict, db: AsyncSession = Depends(get_db)):
    """
    Store a transaction from the frontend, validate it with Paystack, and store the response in the database.
    """
    try:
        # Extract transaction fields
        user_id = transaction_data.get("user_id")
        payment_reference = transaction_data.get("payment_reference")
        plan = transaction_data.get("plan")
        first_name = transaction_data.get("first_name")
        last_name = transaction_data.get("last_name")
        email = transaction_data.get("email")
        payment_status = transaction_data.get("payment_status")
        phone = transaction_data.get("phone")
        country = transaction_data.get("country")
        company_name = transaction_data.get("company_name")
        organization = transaction_data.get("organization")
        site_name = transaction_data.get("site_name")
        quantity = transaction_data.get("quantity")
        amount = transaction_data.get("amount")
        training_and_setup = transaction_data.get("training_and_setup")
        transaction_id = transaction_data.get("transaction_id")
        message = transaction_data.get("message")

        #logging.info(f"Transaction data: {transaction_data}")

        # Check for missing required fields individually and raise detailed errors
        required_fields = {
            "user_id": user_id,
            "plan": plan,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "country": country,
            "company_name": company_name,
            "organization": organization,
            "site_name": site_name,
            "quantity": quantity,
            "amount": amount,
            "training_and_setup": training_and_setup,
            "payment_reference": payment_reference,
            "transaction_id": transaction_id,
            "message": message,
            "payment_status": payment_status,
        }
        

        missing_fields = [field for field, value in required_fields.items() if value is None]
        if missing_fields:
            raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing_fields)}")


        #logging.info(f"Missing fields: {missing_fields}")
        

        # Convert user_id to UUID if it's not already a UUID
        try:
            if not isinstance(user_id, uuid.UUID):
                user_id = uuid.UUID(str(user_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format for user_id")


        # Fetch the user from the database to check if they exist
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

       # Verify payment with Paystack using the security module
        paystack_status, paystack_response = await verify_paystack_transaction(payment_reference)
        
        try:
            transaction_id = int(transaction_data.get("transaction_id"))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail="transaction_id must be a valid integer"
            )


        # Proceed only if Paystack status is "success" or "failed"
        if paystack_status != "success" and paystack_status != "failed":
            raise HTTPException(
                status_code=400, 
                detail="Invalid Paystack transaction status. Please verify your payment reference."
            )
            
        # Dynamically trigger Frappe site creation if Paystack status is "success"
        # if paystack_status == "success":
        #     admin_password = "admin123456789"
        #     mysql_password= "Oreoluwa@555"
        #     frappe_site_creation_response = await create_frappe_site({
        #         "email": email,
        #         "site_name": site_name,
        #         "admin_password": admin_password,
        #         "mysql_password": mysql_password
        #     })

        #     if "status" in frappe_site_creation_response:
        #         if frappe_site_creation_response["status"] == "failed":
        #             raise HTTPException(
        #                 status_code=500,
        #                 detail=frappe_site_creation_response["message"]
        #             )
        #         elif "successfully" in frappe_site_creation_response["message"]:
        #             # Site creation was successful
        #             pass
        #         else:
        #             raise HTTPException(
        #                 status_code=500,
        #                 detail="Unexpected message: " + frappe_site_creation_response["message"]
        #             )
        #     else:
        #         raise HTTPException(
        #             status_code=500,
        #             detail="Unknown error occurred during site creation."
        #         )



        # Create a new transaction record
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
            site_name=site_name,
            quantity=quantity,
            amount=amount,
            training_and_setup=training_and_setup,
            payment_reference=payment_reference,
            transaction_id=transaction_id,
            message=message,
            paystack_status=paystack_status,
            paystack_response=paystack_response,
        )

        # Save the transaction to the database
        db.add(users_transactions)
        logging.info(f"Attempting to save UserTransactions: {users_transactions}")

        await db.commit()
        await db.refresh(users_transactions)
        #Trigger Frappe update
        frappe_response = await store_site_data({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "country": country,
            "company_name": company_name,
            "organization": organization,
            "site_name": site_name,
            "status": payment_status,
            "product": "Hello World!!"
        })

        return {
            "message": "Transaction stored successfully",
            "transaction": {
                "id": users_transactions.id,
                "user_id": str(users_transactions.user_id),
                "plan": users_transactions.plan,
                "payment_status": users_transactions.payment_status,
                "paystack_response": users_transactions.paystack_response,
            },
            "frappe_update_response": frappe_response
        }

    except HTTPException as e:
        logging.error(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"Unhandled error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error storing transaction")
