"""
Admin endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="", tags=["admin"])


@router.post("/day/close")
async def close_day(
    # TODO: Add request body schema
    db: Session = Depends(get_db)
):
    """
    Close day for a sucursal.
    """
    # TODO: Implement day close logic
    raise HTTPException(status_code=501, detail="Not implemented")

