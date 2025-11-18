from fastapi import APIRouter, HTTPException, Depends
from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import ProjectCreate, ProjectSettings
from src.models.index import MessageCreate, MessageRole
from src.rag.retrieval.index import retrieve_context
from src.rag.retrieval.utils import prepare_prompt_and_invoke_llm

router = APIRouter(tags=["projectRoutes"])
"""
`/api/projects`

  - GET `/api/projects/` ~ List all projects
  - POST `/api/projects/` ~ Create a new project
  - DELETE `/api/projects/{project_id}` ~ Delete a specific project
  
  - GET `/api/projects/{project_id}` ~ Get specific project data
  - GET `/api/projects/{project_id}/chats` ~ Get specific project chats
  - GET `/api/projects/{project_id}/settings` ~ Get specific project settings
  
  - PUT `/api/projects/{project_id}/settings` ~ Update specific project settings
  - POST `/api/projects/{project_id}/chats/{chat_id}/messages` ~ Send a message to a Specific Chat
  
"""


@router.get("/")
async def get_projects(current_user_clerk_id: str = Depends(get_current_user_clerk_id)):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Query projects table for projects related to the current user
    * 3. Return projects data
    """
    try:
        projects_query_result = (
            supabase.table("projects")
            .select("*")
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        return {
            "message": "Projects retrieved successfully",
            "data": projects_query_result.data or [],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching projects: {str(e)}",
        )


@router.post("/")
async def create_project(
    project_data: ProjectCreate,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Insert new project into database
    * 3. Check if project creation failed, then return error
    * 4. Create default project settings for the new project
    * 5. Check if project settings creation failed, then rollback the project creation
    * 6. Return newly created project data
    """
    try:
        # Insert new project into database
        project_insert_data = {
            "name": project_data.name,
            "description": project_data.description,
            "clerk_id": current_user_clerk_id,
        }

        project_creation_result = (
            supabase.table("projects").insert(project_insert_data).execute()
        )

        if not project_creation_result.data:
            raise HTTPException(
                status_code=422,
                detail="Failed to create project - invalid data provided",
            )

        newly_created_project = project_creation_result.data[0]

        # Create default project settings for the new project
        project_settings_data = {
            "project_id": newly_created_project["id"],
            "embedding_model": "text-embedding-3-large",
            "rag_strategy": "basic",
            "agent_type": "agentic",
            "chunks_per_search": 10,
            "final_context_size": 5,
            "similarity_threshold": 0.3,
            "number_of_queries": 5,
            "reranking_enabled": True,
            "reranking_model": "reranker-english-v3.0",
            "vector_weight": 0.7,
            "keyword_weight": 0.3,
        }

        project_settings_creation_result = (
            supabase.table("project_settings").insert(project_settings_data).execute()
        )

        if not project_settings_creation_result.data:
            # Rollback: Delete the project if settings creation fails
            supabase.table("projects").delete().eq(
                "id", newly_created_project["id"]
            ).execute()
            raise HTTPException(
                status_code=422,
                detail="Failed to create project settings - project creation rolled back",
            )

        return {
            "message": "Project created successfully",
            "data": newly_created_project,
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while creating project: {str(e)}",
        )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Verify if the project exists and belongs to the current user
    * 3. Delete project - CASCADE will automatically delete all related data:
    * 4. Check if project deletion failed, then return error
    * 5. Return successfully deleted project data
    """
    try:
        # Verify if the project exists and belongs to the current user
        project_ownership_verification_result = (
            supabase.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_ownership_verification_result.data:
            raise HTTPException(
                status_code=404,  # Not Found - project doesn't exist or doesn't belong to user
                detail="Project not found or you don't have permission to delete it",
            )

        # Delete project ~ "CASCADE" will automatically delete all related data: project_settings, project_documents, document_chunks, chats, messages, etc.
        project_deletion_result = (
            supabase.table("projects")
            .delete()
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_deletion_result.data:
            raise HTTPException(
                status_code=500,  # Internal Server Error - deletion failed unexpectedly
                detail="Failed to delete project - please try again",
            )

        successfully_deleted_project = project_deletion_result.data[0]

        return {
            "message": "Project deleted successfully",
            "data": successfully_deleted_project,
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while deleting project: {str(e)}",
        )


@router.get("/{project_id}")
async def get_project(
    project_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Verify if the project exists and belongs to the current user
    * 3. Return project data
    """
    try:
        project_result = (
            supabase.table("projects")
            .select("*")
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_result.data:
            raise HTTPException(
                status_code=404,
                detail="Project not found or you don't have permission to access it",
            )

        return {
            "message": "Project retrieved successfully",
            "data": project_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while retrieving project: {str(e)}",
        )


@router.get("/{project_id}/chats")
async def get_project_chats(
    project_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Verify if the project exists and belongs to the current user
    * 3. Return project chats data
    """
    try:
        project_chats_result = (
            supabase.table("chats")
            .select("*")
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .order("created_at", desc=True)
            .execute()
        )

        # * If there are no chats for the project, return an empty list
        # * A User may or may not have any chats for a project

        return {
            "message": "Project chats retrieved successfully",
            "data": project_chats_result.data or [],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while retrieving project {project_id} chats: {str(e)}",
        )


@router.get("/{project_id}/settings")
async def get_project_settings(
    project_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Verify if the project exists and belongs to the current user
    * 3. Check if the project settings exists for the project
    * 4. Return project settings data
    """
    try:
        project_settings_result = (
            supabase.table("project_settings")
            .select("*")
            .eq("project_id", project_id)
            .execute()
        )

        if not project_settings_result.data:
            raise HTTPException(
                status_code=404,
                detail="Project settings not found or you don't have permission to access it",
            )

        return {
            "message": "Project settings retrieved successfully",
            "data": project_settings_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while retrieving project {project_id} settings: {str(e)}",
        )


@router.put("/{project_id}/settings")
async def update_project_settings(
    project_id: str,
    settings: ProjectSettings,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Verify if the project exists and belongs to the current user
    * 3. Verify if the project settings exist for the project
    * 4. Update project settings
    * 5. Check if project settings update failed, then return error
    * 6. Return successfully updated project settings data
    """
    try:
        project_ownership_verification_result = (
            supabase.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_ownership_verification_result.data:
            raise HTTPException(
                status_code=404,
                detail="Project not found or you don't have permission to update its settings",
            )

        project_settings_ownership_verification_result = (
            supabase.table("project_settings")
            .select("id")
            .eq("project_id", project_id)
            .execute()
        )

        if not project_settings_ownership_verification_result.data:
            raise HTTPException(
                status_code=404,
                detail="Project settings not found for this project",
            )

        project_settings_update_data = (
            settings.model_dump()  # Pydantic modal to dictionary conversion
        )
        project_settings_update_result = (
            supabase.table("project_settings")
            .update(project_settings_update_data)
            .eq("project_id", project_id)
            .execute()
        )

        if not project_settings_update_result.data:
            raise HTTPException(
                status_code=422, detail="Failed to update project settings"
            )

        return {
            "message": "Project settings updated successfully",
            "data": project_settings_update_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while updating project {project_id} settings: {str(e)}",
        )


@router.post("/{project_id}/chats/{chat_id}/messages")
async def send_message(
    project_id: str,
    chat_id: str,
    message: MessageCreate,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    ! Logic Flow:
    * 1. Get current user clerk_id
    * 2. Insert the message into the database.
    * 3. Retrieval
    * 4. Generation (Retrieved Context + User Message)
    * 5. Insert the AI Response into the database.
    """
    try:
        # Step 1 : Insert the message into the database.
        message = message.content
        message_insert_data = {
            "content": message,
            "chat_id": chat_id,
            "clerk_id": current_user_clerk_id,
            "role": MessageRole.USER.value,
        }
        message_creation_result = (
            supabase.table("messages").insert(message_insert_data).execute()
        )

        if not message_creation_result.data:
            raise HTTPException(status_code=422, detail="Failed to create message")

        # Step 3 : Retrieval
        texts, images, tables, citations = retrieve_context(project_id, message)

        # Step 4 : Generation (Retrived Context + User Message)
        final_response = prepare_prompt_and_invoke_llm(
            user_query=message, texts=texts, images=images, tables=tables
        )

        # Step 5: Insert the AI Response into the database.
        ai_response_insert_data = {
            "content": final_response,
            "chat_id": chat_id,
            "clerk_id": current_user_clerk_id,
            "role": MessageRole.ASSISTANT.value,
            "citations": citations,
        }
        ai_response_creation_result = (
            supabase.table("messages").insert(ai_response_insert_data).execute()
        )
        if not ai_response_creation_result.data:
            raise HTTPException(status_code=422, detail="Failed to create AI response")

        return {
            "message": "Message created successfully",
            "data": {
                "userMessage": message_creation_result.data[0],
                "aiMessage": ai_response_creation_result.data[0],
            },
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while creating message: {str(e)}",
        )
