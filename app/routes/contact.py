# pyrefly: ignore [missing-import]
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.models import ContactForm, DeleteContactsRequest
from app.database import get_database
# pyrefly: ignore [missing-import]
from bson.objectid import ObjectId

router = APIRouter()
bearer_scheme = HTTPBearer()


async def verify_access_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized."
        )

    token = credentials.credentials
    session = await db.auth_sessions.find_one({"token": token})
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )

    now = datetime.now(timezone.utc)
    expires_at = session.get("expires_at")
    # Ensure expires_at is timezone-aware for comparison
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not expires_at or expires_at <= now:
        await db.auth_sessions.delete_one({"_id": session["_id"]})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )

    return True

@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def submit_contact(contact: ContactForm):
    print("contact.model_dump() ", contact.model_dump())
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized. Check your MONGODB_URI."
        )

    contact_dict = contact.model_dump()
    
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

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
            try:
                object_ids.append(ObjectId(id_str))
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid ID format: {id_str}")

        result = await db.contacts.delete_many({"_id": {"$in": object_ids}})
        
        return {
            "message": f"Successfully deleted {result.deleted_count} contacts.",
            "deleted_count": result.deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
