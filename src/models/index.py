from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ProjectCreate(BaseModel):
    name: str = Field(..., description="The name of the project")
    description: Optional[str] = Field(None, description="Project description")


class ChatCreate(BaseModel):
    title: str = Field(..., description="The title of the chat")
    project_id: str = Field(..., description="The ID of the project")


class ProjectSettings(BaseModel):
    embedding_model: str = Field(..., description="The embedding model to use")
    rag_strategy: str = Field(..., description="The RAG strategy to use")
    agent_type: str = Field(..., description="The agent type to use")
    chunks_per_search: int = Field(..., description="The number of chunks per search")
    final_context_size: int = Field(..., description="The final context size")
    similarity_threshold: float = Field(..., description="The similarity threshold")
    number_of_queries: int = Field(..., description="The number of queries")
    reranking_enabled: bool = Field(..., description="Whether reranking is enabled")
    reranking_model: str = Field(..., description="The reranking model to use")
    vector_weight: float = Field(..., description="The vector weight")
    keyword_weight: float = Field(..., description="The keyword weight")


class FileUploadRequest(BaseModel):
    filename: str = Field(..., description="The name of the file")
    file_type: str = Field(..., description="The type of the file")
    file_size: int = Field(..., description="The size of the file")


class ProcessingStatus(str, Enum):
    UPLOADING = "uploading"
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    PARTITIONING = "partitioning"
    CHUNKING = "chunking"
    SUMMARISING = "summarising"
    VECTORIZATION = "vectorization"
    COMPLETED = "completed"


class UrlRequest(BaseModel):
    url: str = Field(..., description="The URL to process")


class MessageCreate(BaseModel):
    content: str = Field(..., description="The content of the message")


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class QueryVariations(BaseModel):
    queries: List[str] = Field(..., description="The variations of the query")
