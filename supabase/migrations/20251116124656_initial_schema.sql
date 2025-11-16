-- 001_initial_schema.sql
-- PostgreSQL migration for RAG application with vector search and full-text search

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    clerk_id TEXT NOT NULL REFERENCES users(clerk_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Project settings table
CREATE TABLE project_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
    embedding_model TEXT NOT NULL,
    rag_strategy TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    chunks_per_search INTEGER NOT NULL,
    final_context_size INTEGER NOT NULL,
    similarity_threshold DECIMAL NOT NULL,
    number_of_queries INTEGER NOT NULL,
    reranking_enabled BOOLEAN NOT NULL,
    reranking_model TEXT NOT NULL,
    vector_weight DECIMAL NOT NULL,
    keyword_weight DECIMAL NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Project documents table
CREATE TABLE project_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    processing_status TEXT DEFAULT 'pending',
    task_id TEXT,
    source_type TEXT DEFAULT 'file',
    source_url TEXT,
    processing_details JSON DEFAULT '{}',
    clerk_id TEXT NOT NULL REFERENCES users(clerk_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Document chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES project_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    char_count INTEGER NOT NULL,
    type JSON DEFAULT '{}',
    original_content JSON DEFAULT '{}',
    embedding vector(1536) NOT NULL,
    fts tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Chats table
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    clerk_id TEXT NOT NULL REFERENCES users(clerk_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    clerk_id TEXT NOT NULL REFERENCES users(clerk_id) ON DELETE CASCADE,
    citations JSON DEFAULT '[]',
    trace_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for search performance
CREATE INDEX document_chunks_fts_idx ON document_chunks USING gin (fts);
CREATE INDEX document_chunks_embedding_hnsw_idx ON document_chunks USING hnsw (embedding vector_ip_ops);