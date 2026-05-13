# pyrefly: ignore [missing-import]
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from app.models import ContactForm, DeleteContactsRequest
from app.database import get_database
# pyrefly: ignore [missing-import]
from bson.objectid import ObjectId
from app.limiter import limiter
from app.profanity_filter import validate_profanity
from app.verifyToken import verify_access_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/contact", status_code=status.HTTP_201_CREATED)
@limiter.limit("5 per 15 minutes")
async def submit_contact(contact: ContactForm, request: Request):
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized. Check your MONGODB_URI."
        )

    # Honeypot detection: website field must be empty
    if contact.website:
        logger.warning(f"Honeypot triggered - bot detected (website field filled): {contact.website}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request, Bot Detected"
        )

    # Validate all text fields for profanity
    for field_name in ["name", "email", "query"]:
        field_value = getattr(contact, field_name, "")
        error_msg = validate_profanity(field_value, field_name)
        if error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

    contact_dict = contact.model_dump()
    contact_dict["created_at"] = datetime.now(timezone.utc)

    try:
        # Insert the contact message into the 'contacts' collection
        result = await db.contacts.insert_one(contact_dict)
        if result.inserted_id:
            return {"message": "Contact query submitted successfully!", "id": str(result.inserted_id)}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit contact query."
            )
    except Exception as e:
        logger.exception("Failed to submit contact query.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit contact query."
        ) from e


@router.delete("/contacts", status_code=status.HTTP_200_OK)
async def delete_contacts(
    request: DeleteContactsRequest,
    _: bool = Depends(verify_access_token)
):
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized."
        )

    try:
        object_ids = []
        for id_str in request.ids:
            if not ObjectId.is_valid(id_str):
                raise HTTPException(status_code=400, detail=f"Invalid ID format: {id_str}")
            object_ids.append(ObjectId(id_str))

        result = await db.contacts.delete_many({"_id": {"$in": object_ids}})

        return {
            "message": f"Successfully deleted {result.deleted_count} contacts.",
            "deleted_count": result.deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete contacts.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete contacts."
        ) from e


@router.get("/contacts", status_code=status.HTTP_200_OK)
async def get_contacts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    _: bool = Depends(verify_access_token)
):
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized."
        )

    skip = (page - 1) * limit

    try:
        cursor = db.contacts.find().sort([("created_at", -1)]).skip(skip).limit(limit)
        contacts = await cursor.to_list(length=limit)

        total_contacts = await db.contacts.count_documents({})

        formatted_contacts = []
        for contact in contacts:
            contact["_id"] = str(contact["_id"])

            created_at = contact.get("created_at")
            if created_at and isinstance(created_at, datetime):
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                contact["created_at"] = created_at

            formatted_contacts.append(contact)

        return {
            "data": formatted_contacts,
            "pagination": {
                "total": total_contacts,
                "page": page,
                "limit": limit,
                "total_pages": (total_contacts + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.exception("Failed to retrieve contacts.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contacts."
        ) from e
