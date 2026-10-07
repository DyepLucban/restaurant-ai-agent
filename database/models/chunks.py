from sqlalchemy import ForeignKey, Index, Text, VARCHAR
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from database.connection import Base
from config.settings import EMBEDDING_DIM

class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        Index(
            "ix_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(VARCHAR)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding: Mapped[list[float]] = mapped_column(Vector(int(EMBEDDING_DIM)))