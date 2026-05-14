# pyrefly: ignore [missing-import]
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from app.models import Reaction
from app.database import get_database
# pyrefly: ignore [missing-import]
from bson.objectid import ObjectId
from app.limiter import limiter
from app.verifyToken import verify_access_token

router = APIRouter()
logger = logging.getLogger(__name__)

allowed_reactions = ['Like', 'Celebrate', 'Cheer', 'Appreciate', 'Smile']

@router.post("/reaction", status_code=status.HTTP_201_CREATED)
@limiter.limit("10 per minute")
async def add_reaction(reaction: Reaction, request: Request):
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized. Check your MONGODB_URI."
        )

    reaction_dict = reaction.model_dump()
    reaction_dict["created_at"] = datetime.now(timezone.utc)

    try:

        if reaction_dict["reaction"] not in allowed_reactions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reaction."
            )

        if not reaction_dict["reaction"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data received."
            )

        if not reaction_dict["email"] or not reaction_dict["name"]:
            count_data = await db.reactions.find_one({"reaction": reaction_dict["reaction"], "count": {"$gte": 1}})
            if count_data:
                count_data["count"] += 1
                await db.reactions.update_one({"reaction": reaction_dict["reaction"]}, {"$set": {"count": count_data["count"]}})
                return {"message": "Reaction added successfully!"}
            
        email = await db.reactions.find_one({"email": reaction_dict["email"]})
        if email:
            await db.reactions.update_one({"email": reaction_dict["email"]}, {"$set": {"reaction": reaction_dict["reaction"]}})
            return {"message": "Reaction updated successfully!"}
        
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

@router.get("/reaction", status_code=status.HTTP_200_OK)
async def get_reactions(_: bool = Depends(verify_access_token)):
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is not initialized. Check your MONGODB_URI."
        )

    try:
        pipeline = pipeline = [
            # Normalize: use `count` if present, otherwise 1
            {
                "$addFields": {
                    "effectiveCount": {"$ifNull": ["$count", 1]},
                    "hasEmail": {
                        "$cond": [
                            {"$and": [
                                {"$ifNull": ["$email", False]},
                                {"$ne": ["$email", ""]}
                            ]},
                            1, 0
                        ]
                    }
                }
            },
            # Group by reaction
            {
                "$group": {
                    "_id": "$reaction",
                    "total": {"$sum": "$effectiveCount"},
                    "emailCount": {"$sum": "$hasEmail"}
                }
            },
            # Shape each reaction into {reactionName: count, email: emailCount}
            {
                "$project": {
                    "_id": 0,
                    "reaction": "$_id",
                    "total": 1,
                    "emailCount": 1
                }
            },
            # Group all into one doc to also compute totals
            {
                "$group": {
                    "_id": None,
                    "reactions": {
                        "$push": {
                            "reaction": "$reaction",
                            "total": "$total",
                            "emailCount": "$emailCount"
                        }
                    },
                    "grandTotal": {"$sum": "$total"},
                    "grandEmailCount": {"$sum": "$emailCount"}
                }
            }
        ]
                
        reactions = await db.reactions.aggregate(pipeline).to_list(length=None)
        if not reactions:
            return {"message": "No reactions found."}
        return reactions
    except Exception as e:
        logger.exception("Failed to get reactions.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reactions."
        ) from e
