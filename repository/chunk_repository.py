from fastapi import Depends
from schemas.seats_schema import SeatCreate, SeatUpdate
from database.connection import get_db
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import chunks
from uuid import uuid4
import re

def extract_section(content: str) -> str | None:
    match = re.match(r"\[(.+?)\]", content)
    return match.group(1) if match else None

async def search(query_vector: list[float], db: AsyncSession = Depends(get_db)):
    distance = chunks.Chunk.embedding.cosine_distance(query_vector)

    cols = [
        chunks.Chunk.id,
        chunks.Chunk.uuid,
        chunks.Chunk.content,
        chunks.Chunk.meta,
        (1 - distance).label("similarity"),
    ]

    top = (await db.execute(
        select(*cols).order_by(distance).limit(5)
    )).mappings().all()

    top = [r for r in top if r["similarity"] >= 0.5]
    if not top:
        return []

    sections = {r["meta"]["section"] for r in top}

    expanded = (await db.execute(
        select(*cols)
        .where(chunks.Chunk.meta["section"].as_string().in_(sections))
        .order_by(distance)
    )).mappings().all()

    return expanded

async def read():
    pass

async def edit():
    pass

async def add(data: list, db: AsyncSession = Depends(get_db)):
    uuid = str(uuid4())
    chunk = chunks.Chunk(
        uuid=uuid,
        content=data[0],
        meta=data[2],
        embedding=data[1]
    )

    return chunk

async def delete():
    pass