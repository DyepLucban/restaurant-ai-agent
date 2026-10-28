from fastapi import HTTPException, status, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from repository import table_repository

# Read all records
async def browse(db: AsyncSession = Depends(get_db)):
    try:
        response = await table_repository.browse(db)

        return response
    except SQLAlchemyError as e:
        message = f"Error message: {e}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

# Cheap change fingerprint (count + last write time) used by the UI to detect DB changes
async def version(db: AsyncSession = Depends(get_db)):
    try:
        response = await table_repository.version(db)

        return response
    except SQLAlchemyError as e:
        message = f"Error message: {e}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
