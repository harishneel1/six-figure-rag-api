from fastapi import APIRouter, HTTPException, Depends
from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import ChatCreate

router = APIRouter(tags=["chatRoutes"])

"""
`/api/chats`
    - POST `/api/chats/` ~ Create a new chat
    - DELETE `/api/chats/{chat_id}` ~ Delete a specific chat
"""


@router.post("/")
async def create_chat(
    chat: ChatCreate, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Insert new chat into database
    * 3. Check if chat creation failed, then return error
    * 4. Return successfully created chat data
    """
    try:
        chat_insert_data = {
            "title": chat.title,
            "project_id": chat.project_id,
            "clerk_id": current_user_clerk_id,
        }
        chat_creation_result = (
            supabase.table("chats").insert(chat_insert_data).execute()
        )

        if not chat_creation_result.data:
            raise HTTPException(
                status_code=422, detail="Failed to create chat - invalid data provided"
            )

        return {
            "message": "Chat created successfully",
            "data": chat_creation_result.data[0],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while creating chat: {str(e)}",
        )


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Verify if the chat exists and belongs to the current user
    * 3. Delete chat
    * 4. Return successfully deleted chat data
    """
    try:
        chat_deletion_result = (
            supabase.table("chats")
            .delete()
            .eq("id", chat_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )
        if not chat_deletion_result.data:
            raise HTTPException(
                status_code=404,
                detail="Chat not found or you don't have permission to delete it",
            )

        return {
            "message": "Chat deleted successfully",
            "data": chat_deletion_result.data[0],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while deleting chat {chat_id}: {str(e)}",
        )
