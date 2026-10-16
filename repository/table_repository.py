from fastapi import Depends
from schemas.tables_schema import TableUpdate, TableCreate
from database.connection import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import tables

async def browse(db: AsyncSession = Depends(get_db)):
    tables_record = await db.execute(select(tables.Table))
    response = tables_record.scalars().all()

    return response

async def read(table_id: int, db: AsyncSession = Depends(get_db)):
    table = await db.execute(select(tables.Table).where(tables.Table.id == table_id))
    response = table.scalars().first()

    if not response:
        return None

    return response

async def edit(table_number: int, reserved_date: str, db: AsyncSession = Depends(get_db)):
    model = TableUpdate(is_reserved=True, reserved_date=reserved_date)
    table_record = await db.execute(select(tables.Table).where(tables.Table.table_number == table_number))
    response = table_record.scalars().first()

    if not response:
        return None

    response.is_reserved = model.is_reserved
    response.reserved_date = model.reserved_date

    return response

async def add(model: TableCreate):
    table = tables.Table(
        user_id=model.user_id,
        table_number=model.table_number,
        capacity=model.capacity,
        is_reserved=model.is_reserved,
        reserved_date=model.reserved_date
    )

    return table

async def delete(table_id: int, db: AsyncSession = Depends(get_db)):
    table = await read(table_id, db)

    if not table:
        return None

    await db.delete(table)

    return table