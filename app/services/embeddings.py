# app/services/embeddings.py
from langchain_openai import AzureOpenAIEmbeddings
from app.config.settings import settings

# Single embeddings client. (If not set in .env, raise early)
if not settings.azure_openai_embedding_deployment and not settings.azure_openai_chat_deployment:
    raise RuntimeError("Embedding deployment not configured (AZURE_OPENAI_EMBEDDING_DEPLOYMENT).")

_embeddings = AzureOpenAIEmbeddings(
    azure_deployment=settings.azure_openai_embedding_deployment or settings.azure_openai_chat_deployment,
    api_version=settings.azure_openai_api_version
)

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Returns list of embeddings aligned with input order.
    """
    if not texts:
        return []
    return _embeddings.embed_documents(texts)
