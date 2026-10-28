from fastapi import APIRouter, Depends
from schemas.tables_schema import TableResponse
from sqlalchemy.ext.asyncio import AsyncSession
from controllers import table_controller
from database.connection import get_db

router = APIRouter(prefix="/tables", tags=["tables"])

@router.get("/")
async def browse_tables(db: AsyncSession = Depends(get_db)):
    return await table_controller.browse(db)

@router.get("/version", name="tables_version")
async def tables_version(db: AsyncSession = Depends(get_db)):
    return await table_controller.version(db)
