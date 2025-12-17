from fastapi import APIRouter, HTTPException, Depends
from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import FileUploadRequest, ProcessingStatus, UrlRequest
from src.utils.index import validate_url
from src.config.index import appConfig
from src.services.awsS3 import s3_client
import uuid
from src.services.celery import perform_rag_ingestion_task
from src.config.logging import get_logger, set_project_id

logger = get_logger(__name__)

router = APIRouter(tags=["projectFilesRoutes"])

"""
`/api/projects`

  - GET `/{project_id}/files` ~ List all project files
  - POST `/{project_id}/files/upload-url` ~ Generate presigned url for file upload for frontend
  - POST `/{project_id}/files/confirm` ~ Confirmation of file upload to S3
  - POST `/{project_id}/urls` ~ Add website URL to database
  - DELETE `/{project_id}/files/{file_id}` ~ Delete document from s3 and database
  - GET `/{project_id}/files/{file_id}/chunks` ~ Get project document chunks
"""


@router.get("/{project_id}/files")
async def get_project_files(
    project_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Select all project documents from the project documents table for given project_id
    * 3. Return project documents data
    """
    set_project_id(project_id)
    try:
        logger.info("fetching_project_files", user_id=current_user_clerk_id)
        project_files_result = (
            supabase.table("project_documents")
            .select("*")
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .order("created_at", desc=True)
            .execute()
        )

        # * If there are no project documents for the project, return an empty list
        # * A User may or may not have any project files.

        logger.info("project_files_retrieved", file_count=len(project_files_result.data or []))
        return {
            "message": "Project files retrieved successfully",
            "data": project_files_result.data or [],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("project_files_retrieval_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while retrieving project {project_id} files: {str(e)}",
        )


@router.post("/{project_id}/files/upload-url")
async def get_upload_presigned_url(
    project_id: str,
    file_upload_request: FileUploadRequest,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    ! Logic Flow:
    * 1. Verify project exists and belongs to the current user
    * 2. Generate s3 key
    * 3. Generate upload presigned url (will expire in 1 hour)
    * 4. Create project document record with pending status
    * 5. Return presigned url
    """
    set_project_id(project_id)
    try:
        logger.info("generating_upload_url", filename=file_upload_request.filename, file_size=file_upload_request.file_size)
        # Verify project exists and belongs to the current user
        project_ownership_verification_result = (
            supabase.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_ownership_verification_result.data:
            logger.warning("project_not_found_for_upload", user_id=current_user_clerk_id)
            raise HTTPException(
                status_code=404,
                detail="Project not found or you don't have permission to upload files to this project",
            )

        # Generate s3 key
        file_extension = (
            file_upload_request.filename.split(".")[-1]
            if "." in file_upload_request.filename
            else ""
        )
        unique_file_id = uuid.uuid4()
        s3_key = (
            f"projects/{project_id}/documents/{unique_file_id}.{file_extension}"
            if file_extension
            else f"projects/{project_id}/documents/{unique_file_id}"
        )

        # Generate upload presigned url (will expire in 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": appConfig["s3_bucket_name"],
                "Key": s3_key,
                "ContentType": file_upload_request.file_type,
            },
            ExpiresIn=3600,  # 1 hour
        )

        if not presigned_url:
            logger.error("presigned_url_generation_failed", s3_key=s3_key)
            raise HTTPException(
                status_code=422,
                detail="Failed to generate upload presigned url",
            )

        # Generate database record with pending status
        document_creation_result = (
            supabase.table("project_documents")
            .insert(
                {
                    "project_id": project_id,
                    "filename": file_upload_request.filename,
                    "s3_key": s3_key,
                    "file_size": file_upload_request.file_size,
                    "file_type": file_upload_request.file_type,
                    "processing_status": ProcessingStatus.PENDING,
                    "clerk_id": current_user_clerk_id,
                }
            )
            .execute()
        )

        if not document_creation_result.data:
            logger.error("document_record_creation_failed", filename=file_upload_request.filename, reason="no_data_returned")
            raise HTTPException(
                status_code=422,
                detail="Failed to create project document - invalid data provided",
            )

        logger.info("upload_url_generated_successfully", document_id=document_creation_result.data[0]["id"], s3_key=s3_key)
        return {
            "message": "Upload presigned url generated successfully",
            "data": {
                "upload_url": presigned_url,
                "s3_key": s3_key,
                "document": document_creation_result.data[0],
            },
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("upload_url_generation_error", filename=file_upload_request.filename, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while generating upload presigned url for {project_id}: {str(e)}",
        )


@router.post("/{project_id}/files/confirm")
async def confirm_file_upload_to_s3(
    project_id: str,
    confirm_file_upload_request: dict,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    ! Logic Flow:
    * 1. Verify S3 key is provided
    * 2. Verify file exists in database
    * 3. Update file status to "queued"
    * 4. Perform Celery - RAG Ingestion Task
    * 5. Update the project document record with the task_id
    * 6. Return successfully confirmed file upload data
    """
    set_project_id(project_id)
    try:
        s3_key = confirm_file_upload_request.get("s3_key")
        logger.info("confirming_file_upload", s3_key=s3_key)
        if not s3_key:
            logger.warning("s3_key_missing")
            raise HTTPException(
                status_code=400,
                detail="S3 key is required",
            )

        # Verify file exists in database
        document_verification_result = (
            supabase.table("project_documents")
            .select("id")
            .eq("s3_key", s3_key)
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not document_verification_result.data:
            logger.warning("file_not_found_for_confirmation", s3_key=s3_key)
            raise HTTPException(
                status_code=404,
                detail="File not found or you don't have permission to confirm upload to S3 for this file",
            )

        # Update file status to "queued"
        document_update_result = (
            supabase.table("project_documents")
            .update(
                {
                    "processing_status": ProcessingStatus.QUEUED,
                }
            )
            .eq("s3_key", s3_key)
            .execute()
        )

        # ! Celery - Starts Background Processing - RAG Ingestion Task
        document_id = document_update_result.data[0]["id"]
        task_result = perform_rag_ingestion_task.delay(document_id)
        task_id = task_result.id
        logger.info("rag_ingestion_task_queued", document_id=document_id, task_id=task_id)

        document_update_result = (
            supabase.table("project_documents")
            .update(
                {
                    "task_id": task_id,
                }
            )
            .eq("id", document_id)
            .execute()
        )
        if not document_update_result.data:
            logger.error("task_id_update_failed", document_id=document_id, task_id=task_id, reason="no_data_returned")
            raise HTTPException(
                status_code=422,
                detail="Failed to update project document record with task_id",
            )

        logger.info("file_upload_confirmed_successfully", document_id=document_id, task_id=task_id)
        return {
            "message": "File upload to S3 confirmed successfully And Started Background Pre-Processing of this file",
            "data": document_update_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("file_confirmation_error", s3_key=s3_key, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while confirming upload to S3 for {project_id}: {str(e)}",
        )


@router.post("/{project_id}/urls")
async def process_url(
    project_id: str,
    url: UrlRequest,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    ! Logic Flow:
    * 1. Validate URL
    * 2. Add website URL to database
    * 3. Start background pre-processing of this URL
    * 4. Return successfully processed URL data
    """
    set_project_id(project_id)
    try:
        # Validate URL
        url = url.url
        if url.startswith("http://") or url.startswith("https://"):
            url = url
        else:
            url = f"https://{url}"

        logger.info("processing_url", url=url)
        if not validate_url(url):
            logger.warning("invalid_url", url=url)
            raise HTTPException(
                status_code=400,
                detail="Invalid URL",
            )

        # Add website Url to database
        document_creation_result = (
            supabase.table("project_documents")
            .insert(
                {
                    "project_id": project_id,
                    "filename": url,
                    "s3_key": "",
                    "file_size": 0,
                    "file_type": "text/html",
                    "processing_status": ProcessingStatus.QUEUED,
                    "clerk_id": current_user_clerk_id,
                    "source_type": "url",
                    "source_url": url,
                }
            )
            .execute()
        )

        if not document_creation_result.data:
            logger.error("url_document_creation_failed", url=url, reason="no_data_returned")
            raise HTTPException(
                status_code=422,
                detail="Failed to create project document with URL Record - invalid data provided",
            )

        # ! Celery - Starts Background Processing - RAG Ingestion Task
        document_id = document_creation_result.data[0]["id"]
        task_result = perform_rag_ingestion_task.delay(document_id)
        task_id = task_result.id
        logger.info("url_ingestion_task_queued", document_id=document_id, task_id=task_id, url=url)

        document_update_result = (
            supabase.table("project_documents")
            .update(
                {
                    "task_id": task_id,
                }
            )
            .eq("id", document_id)
            .execute()
        )

        if not document_update_result.data:
            logger.error("url_task_id_update_failed", document_id=document_id, task_id=task_id, reason="no_data_returned")
            raise HTTPException(
                status_code=422,
                detail="Failed to update project document record with task_id",
            )

        logger.info("url_processed_successfully", document_id=document_id, url=url, task_id=task_id)
        return {
            "message": "Website URL added to database successfully And Started Background Pre-Processing of this URL",
            "data": document_creation_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("url_processing_error", url=url, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while processing urls for {project_id}: {str(e)}",
        )


@router.delete("/{project_id}/files/{file_id}")
async def delete_project_document(
    project_id: str,
    file_id: str,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    ! Logic Flow:
    * 1. Verify document exists and belongs to the current user and take complete project document record
    * 2. Delete file from S3 (only for actual files, not for URLs)
    * 3. Delete document from database
    * 4. Return successfully deleted document data
    """
    set_project_id(project_id)
    try:
        logger.info("deleting_document", file_id=file_id, user_id=current_user_clerk_id)
        # Verify document exists and belongs to the current user and Take complete project document record
        document_ownership_verification_result = (
            supabase.table("project_documents")
            .select("*")
            .eq("id", file_id)
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not document_ownership_verification_result.data:
            logger.warning("document_not_found_for_deletion", file_id=file_id)
            raise HTTPException(
                status_code=404,
                detail="Document not found or you don't have permission to delete this document",
            )

        # Delete file from S3 (only for actual files, not for URLs)
        s3_key = document_ownership_verification_result.data[0]["s3_key"]
        if s3_key:
            logger.info("deleting_from_s3", file_id=file_id, s3_key=s3_key)
            s3_client.delete_object(Bucket=appConfig["s3_bucket_name"], Key=s3_key)

        # Delete document from database
        document_deletion_result = (
            supabase.table("project_documents")
            .delete()
            .eq("id", file_id)
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not document_deletion_result.data:
            logger.error("document_deletion_failed", file_id=file_id, reason="no_data_returned")
            raise HTTPException(
                status_code=404,
                detail="Failed to delete document",
            )

        logger.info("document_deleted_successfully", file_id=file_id)
        return {
            "message": "Document deleted successfully",
            "data": document_deletion_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("document_deletion_error", file_id=file_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while deleting project document {file_id} for {project_id}: {str(e)}",
        )


@router.get("/{project_id}/files/{file_id}/chunks")
async def get_project_document_chunks(
    project_id: str,
    file_id: str,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    ! Logic Flow:
    * 1. Verify document exists and belongs to the current user and Take complete project document record
    * 2. Get project document chunks
    * 3. Return project document chunks data
    """
    set_project_id(project_id)
    try:
        logger.info("fetching_document_chunks", file_id=file_id, user_id=current_user_clerk_id)
        # Verify document exists and belongs to the current user and Take complete project document record
        document_ownership_verification_result = (
            supabase.table("project_documents")
            .select("*")
            .eq("id", file_id)
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not document_ownership_verification_result.data:
            logger.warning("document_not_found_for_chunks", file_id=file_id)
            raise HTTPException(
                status_code=404,
                detail="Document not found or you don't have permission to delete this document",
            )

        document_chunks_result = (
            supabase.table("document_chunks")
            .select("*")
            .eq("document_id", file_id)
            .order("chunk_index")
            .execute()
        )

        logger.info("document_chunks_retrieved", file_id=file_id, chunk_count=len(document_chunks_result.data or []))
        return {
            "message": "Project document chunks retrieved successfully",
            "data": document_chunks_result.data or [],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("document_chunks_retrieval_error", file_id=file_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while getting project document chunks for {file_id} for {project_id}: {str(e)}",
        )
