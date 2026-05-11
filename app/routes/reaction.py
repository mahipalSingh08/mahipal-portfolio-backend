# pyrefly: ignore [missing-import]
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.models import Reaction
from app.database import get_database
# pyrefly: ignore [missing-import]
from bson.objectid import ObjectId

router = APIRouter()
bearer_scheme = HTTPBearer()
logger = logging.getLogger(__name__)


@router.post("/reaction", status_code=status.HTTP_201_CREATED)
async def add_reaction(reaction: Reaction):
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized. Check your MONGODB_URI."
        )

    reaction_dict = reaction.model_dump()
    reaction_dict["created_at"] = datetime.now(timezone.utc)

    try:
        # Insert the reaction into the 'reactions' collection
        result = await db.reactions.insert_one(reaction_dict)
        if result.inserted_id:
            return {"message": "Reaction added successfully!", "id": str(result.inserted_id)}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add reaction."
            )
    except Exception as e:
        logger.exception("Failed to add reaction.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add reaction."
        ) from e
