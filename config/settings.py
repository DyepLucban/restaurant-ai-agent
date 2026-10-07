from dotenv import load_dotenv
import os

load_dotenv()

# --- DATABASE
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- LLM/EMBEDDING MODELS
RUNNER_MODEL_BASE_URL = os.getenv("RUNNER_MODEL_BASE_URL")
RUNNER_MODEL = os.getenv("RUNNER_MODEL")
RUNNER_EMBEDDING_MODEL = os.getenv("RUNNER_EMBEDDING_MODEL")
EMBEDDING_DIM = os.getenv("EMBEDDING_DIM")
