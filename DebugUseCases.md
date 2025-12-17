STORY 1: SUCCESS - Complete User Journey
Sarah, a research analyst, creates a new project called "R&D-Analysis". She uploads a 3.2MB PDF file named "research_doc.pdf" containing 143 elements (115 text blocks, 18 tables, 10 images). The system processes it into 20 chunks, vectorizes them in 2 batches, and stores everything in the database. After processing completes, Sarah creates a chat called "Research Questions" and asks "What are the key findings in the research?". The AI agent responds with 387 characters and 3 citations. She then asks a follow-up question "Tell me more about the methodology" and gets a 512 character response with 5 citations.

Log Flow:
    request_started
    creating_project (name: R&D-Analysis)
    project_created (project_id: proj_abc123)
    project_created_successfully
    request_completed

    request_started
    generating_upload_url (filename: research_doc.pdf, file_size: 3355443)
    upload_url_generated_successfully (document_id: doc_xyz789)
    request_completed

    request_started
    confirming_file_upload (s3_key: projects/proj_abc123/documents/doc_xyz789.pdf)
    rag_ingestion_task_queued (document_id: doc_xyz789, task_id: celery_task_456)
    file_upload_confirmed_successfully
    request_completed

    task_started (task_id: celery_task_456, task_name: perform_rag_ingestion_task)
    processing_document (document_id: doc_xyz789)
    document_processing_started (document_id: doc_xyz789)
    updating_document_status (status: processing)
    document_retrieved (source_type: file)
    updating_document_status (status: partitioning)
    downloading_from_s3 (s3_key: projects/proj_abc123/documents/doc_xyz789.pdf)
    s3_download_completed
    elements_analyzed (elements_count: 143)
    partitioning_completed (elements_summary: {text: 115, tables: 18, images: 10})
    updating_document_status (status: chunking)
    chunking_completed (total_chunks: 20)
    updating_document_status (status: summarising)
    updating_document_status (current_chunk: 1, total_chunks: 20)
    updating_document_status (current_chunk: 2, total_chunks: 20)

    updating_document_status (current_chunk: 20, total_chunks: 20)
    summarization_completed (chunks_count: 20)
    updating_document_status (status: vectorization)
    vectorization_started (total_chunks: 20, batch_size: 10)
    batch_vectorized (batch: 1/2)
    batch_vectorized (batch: 2/2)
    storing_chunks_started (total_chunks: 20)
    chunks_stored_successfully (stored_count: 20)
    vectorization_completed (stored_chunks: 20)
    updating_document_status (status: completed)
    document_processing_completed (chunks_created: 20)
    document_processed_successfully (document_id: doc_xyz789, chunks_created: 20)
    task_completed (task_id: celery_task_456, task_name: perform_rag_ingestion_task, state: SUCCESS)

    request_started
    creating_chat (title: Research Questions)
    chat_created_successfully (chat_id: chat_def456)
    request_completed

    request_started
    sending_message (message_length: 43)
    user_message_created (message_id: msg_001)
    fetching_project_settings
    project_settings_retrieved (rag_strategy: basic)
    agent_type_determined (agent_type: agentic)
    chat_history_retrieved (history_length: 0)
    invoking_agent
    agent_invocation_completed (response_length: 387, citations_count: 3)
    message_sent_successfully (ai_message_id: msg_002)
    request_completed

    request_started
    sending_message (message_length: 38)
    user_message_created (message_id: msg_003)
    agent_type_determined (agent_type: agentic)
    chat_history_retrieved (history_length: 2)
    invoking_agent
    agent_invocation_completed (response_length: 512, citations_count: 5)
    message_sent_successfully (ai_message_id: msg_004)
    request_completed


STORY 2: FAILURE - OpenAI Rate Limit
Maria uploads a large "annual_report.pdf" with 200 pages during peak traffic hours. The file successfully partitions into 87 elements and chunks into 45 pieces. All 45 chunks get AI summaries. However, when vectorization starts, the first batch of 10 chunks hits OpenAI's rate limit. The system retries 3 times with exponential backoff (2s, 4s) but all attempts fail due to rate limiting. The entire document processing fails.

Log Flow:
    
    request_started
    confirming_file_upload
    rag_ingestion_task_queued (document_id: doc_large777, task_id: celery_task_888)
    file_upload_confirmed_successfully
    request_completed

    task_started (task_id: celery_task_888, task_name: perform_rag_ingestion_task)
    processing_document (document_id: doc_large777)
    document_processing_started (document_id: doc_large777)
    updating_document_status (status: processing)
    document_retrieved (source_type: file)
    updating_document_status (status: partitioning)
    downloading_from_s3
    s3_download_completed
    elements_analyzed (elements_count: 87)
    partitioning_completed (elements_summary: {text: 69, tables: 12, images: 6})
    updating_document_status (status: chunking)
    chunking_completed (total_chunks: 45)
    updating_document_status (status: summarising)
    updating_document_status (current_chunk: 1, total_chunks: 45)
    
    updating_document_status (current_chunk: 45, total_chunks: 45)
    summarization_completed (chunks_count: 45)
    updating_document_status (status: vectorization)
    vectorization_started (total_chunks: 45, batch_size: 10)
    vectorization_retry (batch: 1, attempt: 1, wait_seconds: 2)
    vectorization_retry (batch: 1, attempt: 2, wait_seconds: 4)
    vectorization_batch_failed (batch: 1, attempt: 3, error: Rate limit reached)
    vectorization_and_storage_failed
    document_processing_failed (document_id: doc_large777)
    document_processing_failed (document_id: doc_large777, error: Failed to process document)
    task_failed (task_id: celery_task_888, task_name: perform_rag_ingestion_task)
