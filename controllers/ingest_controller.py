from services.document_chunking_service import chunk_document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from database.connection import SessionAsync
from repository.chunk_repository import add
from services.embedding_service import embed_text
from fastapi import UploadFile, HTTPException, status
from pypdf import PdfReader
from uuid import uuid4
import io

async def read_file(file: UploadFile):
    uuid = str(uuid4()) 
    contents = await file.read()
    pdf_stream = io.BytesIO(contents)
    reader = PdfReader(pdf_stream)

    text = "\n".join(page.extract_text() for page in reader.pages)
    chunks = chunk_document(text, file.filename)
    embedded_data = await embed_text(chunks)

    async with SessionAsync() as db:
        try:
            for item in embedded_data:
                response = await add(item, db)
                db.add(response)

            await db.commit()

            return {"is_ingested": True}
        except SQLAlchemyError as e:
            message = f"Error message: {e}"
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=message
            )
