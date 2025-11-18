# TODO : To remove unnecessary imports
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import ProjectCreate

router = APIRouter(tags=["projectFilesRoutes"])

"""
`/api/projects`

  - GET `/{project_id}/files` ~ List all project files
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
    try:
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

        return {
            "message": "Project files retrieved successfully",
            "data": project_files_result.data or [],
        }
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while retrieving project {project_id} files: {str(e)}",
        )
