from typing import Optional

from qdrant_client import QdrantClient
from langchain_community.vectorstores import Qdrant
from langchain.embeddings.base import Embeddings

from app.config import settings


def get_qdrant_client() -> QdrantClient:
    """
    Create a Qdrant client using settings, with safe defaults.

    This keeps Qdrant configuration centralized and makes it easy
    to swap between local and hosted deployments.
    """
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, prefer_grpc=False)


def get_qdrant_vectorstore(
    embeddings: Embeddings,
    collection_name: str = "richtv_docs",
) -> Qdrant:
    """
    Return a LangChain Qdrant vector store instance.

    The caller is responsible for providing an Embeddings implementation
    (e.g., OpenAI, Gemini, or a custom model) so the LLM backend remains
    fully pluggable.
    """
    client = get_qdrant_client()

    return Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings,
    )

