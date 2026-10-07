from config.settings import RUNNER_EMBEDDING_MODEL, RUNNER_MODEL_BASE_URL, EMBEDDING_DIM
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import TokenTextSplitter

embedding_model = OpenAIEmbeddings(
    model=RUNNER_EMBEDDING_MODEL,
    base_url=RUNNER_MODEL_BASE_URL,
    api_key="not-needed",
    check_embedding_ctx_length=False
)
splitter = TokenTextSplitter(chunk_size=300, chunk_overlap=30)

# Embed document contents
async def embed_text(chunks: list):
    texts, metadatas = [], []
    for data in chunks:
        text = data["text"]
        for sub_text in splitter.split_text(text):
            texts.append(sub_text)
            metadatas.append(data["metadata"])

    vectors = await embedding_model.aembed_documents(
        [f"searched document: {t}" for t in texts]
    )

    return list(zip(texts, vectors, metadatas))

# Embed user's query
async def embed_query(query: str) -> list[float]:
    QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
    return await embedding_model.aembed_query(QUERY_PREFIX + query)
