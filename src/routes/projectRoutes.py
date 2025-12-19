from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends
from src.agents.simple_agent.agent import create_simple_rag_agent
from src.agents.supervisor_agent.agent import create_supervisor_agent

from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import ProjectCreate, ProjectSettings
from src.models.index import MessageCreate, MessageRole
from src.config.logging import get_logger, set_project_id, set_user_id

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import json

logger = get_logger(__name__)

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
    set_user_id(current_user_clerk_id)
    try:
        logger.info("fetching_projects")
        projects_query_result = (
            supabase.table("projects")
            .select("*")
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        logger.info("projects_retrieved", project_count=len(projects_query_result.data or []))
        return {
            "message": "Projects retrieved successfully",
            "data": projects_query_result.data or [],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("projects_fetch_failed", error=str(e), exc_info=True)
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
    set_user_id(current_user_clerk_id)
    try:
        logger.info("creating_project", name=project_data.name)
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
            logger.error("project_creation_failed", name=project_data.name, reason="no_data_returned")
            raise HTTPException(
                status_code=422,
                detail="Failed to create project - invalid data provided",
            )

        newly_created_project = project_creation_result.data[0]
        set_project_id(newly_created_project["id"])
        logger.info("project_created", name=project_data.name)

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
            logger.error("project_settings_creation_failed", reason="no_data_returned")
            # Rollback: Delete the project if settings creation fails
            supabase.table("projects").delete().eq(
                "id", newly_created_project["id"]
            ).execute()
            raise HTTPException(
                status_code=422,
                detail="Failed to create project settings - project creation rolled back",
            )

        logger.info("project_created_successfully", name=project_data.name)
        return {
            "message": "Project created successfully",
            "data": newly_created_project,
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("project_creation_error", name=project_data.name, error=str(e), exc_info=True)
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
    set_project_id(project_id)
    set_user_id(current_user_clerk_id)
    try:
        logger.info("deleting_project")
        # Verify if the project exists and belongs to the current user
        project_ownership_verification_result = (
            supabase.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_ownership_verification_result.data:
            logger.warning("project_not_found_or_unauthorized")
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
            logger.error("project_deletion_failed", reason="no_data_returned")
            raise HTTPException(
                status_code=500,  # Internal Server Error - deletion failed unexpectedly
                detail="Failed to delete project - please try again",
            )

        successfully_deleted_project = project_deletion_result.data[0]

        logger.info("project_deleted_successfully")
        return {
            "message": "Project deleted successfully",
            "data": successfully_deleted_project,
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("project_deletion_error", error=str(e), exc_info=True)
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
    set_project_id(project_id)
    set_user_id(current_user_clerk_id)
    try:
        logger.info("fetching_project")
        project_result = (
            supabase.table("projects")
            .select("*")
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_result.data:
            logger.warning("project_not_found")
            raise HTTPException(
                status_code=404,
                detail="Project not found or you don't have permission to access it",
            )

        logger.info("project_retrieved")
        return {
            "message": "Project retrieved successfully",
            "data": project_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("project_retrieval_error", error=str(e), exc_info=True)
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
    set_project_id(project_id)
    set_user_id(current_user_clerk_id)
    try:
        logger.info("fetching_project_chats")
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

        logger.info("project_chats_retrieved", chat_count=len(project_chats_result.data or []))
        return {
            "message": "Project chats retrieved successfully",
            "data": project_chats_result.data or [],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("project_chats_retrieval_error", error=str(e), exc_info=True)
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
    set_project_id(project_id)
    set_user_id(current_user_clerk_id)
    try:
        logger.info("fetching_project_settings")
        project_settings_result = (
            supabase.table("project_settings")
            .select("*")
            .eq("project_id", project_id)
            .execute()
        )

        if not project_settings_result.data:
            logger.warning("project_settings_not_found")
            raise HTTPException(
                status_code=404,
                detail="Project settings not found or you don't have permission to access it",
            )

        settings_data = project_settings_result.data[0]
        logger.info("project_settings_retrieved",
                   rag_strategy=settings_data.get("rag_strategy"),
                   agent_type=settings_data.get("agent_type"),
                   embedding_model=settings_data.get("embedding_model"),
                   final_context_size=settings_data.get("final_context_size"),
                   reranking_enabled=settings_data.get("reranking_enabled"))
        return {
            "message": "Project settings retrieved successfully",
            "data": project_settings_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("project_settings_retrieval_error", error=str(e), exc_info=True)
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
    set_project_id(project_id)
    set_user_id(current_user_clerk_id)
    try:
        logger.info("updating_project_settings",
                   rag_strategy=settings.rag_strategy,
                   agent_type=settings.agent_type,
                   embedding_model=settings.embedding_model,
                   final_context_size=settings.final_context_size,
                   reranking_enabled=settings.reranking_enabled)
        project_ownership_verification_result = (
            supabase.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_ownership_verification_result.data:
            logger.warning("project_not_found_for_settings_update")
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
            logger.warning("project_settings_not_found_for_update")
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
            logger.error("project_settings_update_failed", reason="no_data_returned")
            raise HTTPException(
                status_code=422, detail="Failed to update project settings"
            )

        logger.info("project_settings_updated_successfully",
                   rag_strategy=settings.rag_strategy,
                   agent_type=settings.agent_type,
                   embedding_model=settings.embedding_model,
                   final_context_size=settings.final_context_size,
                   reranking_enabled=settings.reranking_enabled)
        return {
            "message": "Project settings updated successfully",
            "data": project_settings_update_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error("project_settings_update_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while updating project {project_id} settings: {str(e)}",
        )

def get_chat_history(chat_id: str, exclude_message_id: str = None) -> List[Dict[str, str]]:
    """
    Fetch and format chat history for agent context.
    
    Retrieves the last 10 messages (5 user + 5 assistant) from the chat,
    excluding the current message being processed.
    
    Args:
        chat_id: The ID of the chat
        exclude_message_id: Optional message ID to exclude from history
        
    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    try:
        query = (
            supabase.table("messages")
            .select("id, role, content")
            .eq("chat_id", chat_id)
            .order("created_at", desc=False)
        )
        
        # Exclude current message if provided
        if exclude_message_id:
            query = query.neq("id", exclude_message_id)
        
        messages_result = query.execute()
        
        if not messages_result.data:
            return []
        
        # Get last 10 messages (limit to 10 total messages)
        recent_messages = messages_result.data[-10:]
        
        # Format messages for agent
        formatted_history = []
        for msg in recent_messages:
            formatted_history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        return formatted_history
    except Exception:
        # If history retrieval fails, return empty list
        return []



@router.post("/{project_id}/chats/{chat_id}/messages")
async def send_message(
    project_id: str,
    chat_id: str,
    message: MessageCreate,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    Step 1 : Insert the message into the database.
    Step 2 : Get user's project settings from the database (to retrieve agent_type).
    Step 3 : Get chat history for context.
    Step 4 : Invoke the simple agent with the user's message.
    Step 5 : Insert the AI Response into the database after invocation completes.

    Returns a JSON response with the user message and AI response.
    """
    set_project_id(project_id)
    set_user_id(current_user_clerk_id)
    try:
        logger.info("sending_message", chat_id=chat_id)
        # Step 1 : Insert the message into the database.
        message_content = message.content
        message_insert_data = {
            "content": message_content,
            "chat_id": chat_id,
            "clerk_id": current_user_clerk_id,
            "role": MessageRole.USER.value,
        }
        message_creation_result = (
            supabase.table("messages").insert(message_insert_data).execute()
        )
        if not message_creation_result.data:
            logger.error("message_creation_failed", chat_id=chat_id, reason="no_data_returned")
            raise HTTPException(status_code=422, detail="Failed to create message")

        current_message_id = message_creation_result.data[0]["id"]
        logger.info("user_message_created", message_id=current_message_id, chat_id=chat_id)

        # Step 2 : Get project settings to retrieve agent_type
        try:
            project_settings = await get_project_settings(project_id, current_user_clerk_id)
            agent_type = project_settings["data"].get("agent_type", "simple")
        except Exception as e:
            logger.warning("settings_retrieval_failed_defaulting_to_simple", error=str(e))
            agent_type = "simple"

        logger.info("agent_type_determined", agent_type=agent_type)
        # Step 3 : Get chat history (excluding current message)
        chat_history = get_chat_history(chat_id, exclude_message_id=current_message_id)
        logger.info("chat_history_retrieved", chat_id=chat_id, history_length=len(chat_history))

        # Step 4: Invoke the appropriate agent based on agent_type
        if agent_type == "simple":
            agent = create_simple_rag_agent(
                project_id=project_id,
                model="gpt-4o",
                chat_history=chat_history
            )
        elif agent_type == "agentic":
            agent = create_supervisor_agent(
                project_id=project_id,
                model="gpt-4o",
                chat_history=chat_history
            )

        logger.info("invoking_agent", chat_id=chat_id, agent_type=agent_type)
        # Invoke the agent with the user's message
        result = agent.invoke({
            "messages": [{"role": "user", "content": message_content}]
        })

        # Extract the final response and citations from the result
        final_response = result["messages"][-1].content
        citations = result.get("citations", [])
        logger.info("agent_invocation_completed", chat_id=chat_id, response_length=len(final_response), citations_count=len(citations))

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
            logger.error("ai_response_creation_failed", chat_id=chat_id, reason="no_data_returned")
            raise HTTPException(status_code=422, detail="Failed to create AI response")

        logger.info("message_sent_successfully", chat_id=chat_id, ai_message_id=ai_response_creation_result.data[0]["id"])
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
        logger.error("send_message_error", chat_id=chat_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while creating message: {str(e)}",
        )


@router.post("/{project_id}/chats/{chat_id}/messages/stream")
async def stream_message(
    project_id: str,
    chat_id: str,
    message: MessageCreate,
    clerk_id: str = Query(..., description="Clerk user ID"),
):
    """
    Stream a message response using Server-Sent Events.
    """

    set_project_id(project_id)  
    set_user_id(clerk_id)  
    
    async def event_generator():
        try:
            logger.info("sending_message", chat_id=chat_id)

            # Step 1: Insert user message into database
            message_content = message.content
            message_insert_data = {
                "content": message_content,
                "chat_id": chat_id,
                "clerk_id": clerk_id,
                "role": MessageRole.USER.value,
            }
            message_creation_result = (
                supabase.table("messages").insert(message_insert_data).execute()
            )
            if not message_creation_result.data:
                logger.error("message_creation_failed", chat_id=chat_id, reason="no_data_returned") 
                yield f"event: error\ndata: {json.dumps({'message': 'Failed to create message'})}\n\n"
                return
            
            user_message_data = message_creation_result.data[0]
            current_message_id = user_message_data["id"]
            logger.info("user_message_created", message_id=current_message_id, chat_id=chat_id)  # Added: Success log
            
            # Step 2: Get project settings for agent_type
            try:
                project_settings = await get_project_settings(project_id)
                agent_type = project_settings["data"].get("agent_type", "simple")
            except Exception as e:
                logger.warning("settings_retrieval_failed_defaulting_to_simple", error=str(e))
                agent_type = "simple"

            logger.info("agent_type_determined", agent_type=agent_type)
            
            # Step 3: Get chat history
            chat_history = get_chat_history(chat_id, exclude_message_id=current_message_id)
            logger.info("chat_history_retrieved", chat_id=chat_id, history_length=len(chat_history))  # Added: Chat history log
            
            # Step 4: Create the appropriate agent
            if agent_type == "simple":
                agent = create_simple_rag_agent(
                    project_id=project_id,
                    model="gpt-4o",
                    chat_history=chat_history
                )
            else:  # agentic
                agent = create_supervisor_agent(
                    project_id=project_id,
                    model="gpt-4o",
                    chat_history=chat_history
                )

            logger.info("invoking_agent", chat_id=chat_id, agent_type=agent_type)
            
            # Step 5: Stream the agent response
            full_response = ""
            citations = []
            
            # Track state to know when we're in the final response
            passed_guardrail = False
            tool_called = False
            is_final_response = False
            
            async for event in agent.astream_events(
                {"messages": [{"role": "user", "content": message_content}]},
                version="v2"
            ):
                kind = event["event"]
                tags = event.get("tags", [])
                name = event.get("name", "")
                
                # Detect guardrail completion
                if kind == "on_chain_end" and name == "guardrail":
                    # Check if guardrail rejected the input
                    output = event.get("data", {}).get("output", {})
                    if output.get("guardrail_passed") == False:
                        # Stream the rejection message
                        messages = output.get("messages", [])
                        if messages:
                            rejection_content = messages[0].content if hasattr(messages[0], 'content') else str(messages[0])
                            full_response = rejection_content
                            yield f"event: token\ndata: {json.dumps({'content': rejection_content})}\n\n"
                    else:
                        passed_guardrail = True
                        yield f"event: status\ndata: {json.dumps({'status': 'Thinking...'})}\n\n"
                
                # Status updates for tool calls
                elif kind == "on_tool_start":
                    tool_called = True
                    tool_name = name
                    if tool_name == "rag_search":
                        yield f"event: status\ndata: {json.dumps({'status': 'Searching documents...'})}\n\n"
                    elif tool_name == "search_web":
                        yield f"event: status\ndata: {json.dumps({'status': 'Searching the web...'})}\n\n"
                
                # Detect when tool ends - next model call will be the final response
                elif kind == "on_tool_end":
                    is_final_response = True
                    yield f"event: status\ndata: {json.dumps({'status': 'Generating response...'})}\n\n"
                
                # Stream tokens from the model
                elif kind == "on_chat_model_stream":
                    # Stream if:
                    # 1. Guardrail passed AND
                    # 2. Either tool finished OR no tool was called yet AND
                    # 3. Has the seq:step:1 tag (part of main agent flow, not nested LLM)
                    if passed_guardrail and (is_final_response or not tool_called) and 'seq:step:1' in tags:
                        chunk = event["data"].get("chunk")
                        if chunk:
                            content = chunk.content if hasattr(chunk, 'content') else ""
                            if content:
                                full_response += content
                                yield f"event: token\ndata: {json.dumps({'content': content})}\n\n"
                
                # Capture citations from the final state
                elif kind == "on_chain_end" and name == "LangGraph" and tags == []:
                    # This is the outermost LangGraph ending
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict) and "citations" in output:
                        citations = output["citations"]
            
            logger.info("agent_invocation_completed", chat_id=chat_id, response_length=len(full_response), citations_count=len(citations))  # Added: Completion log
            
            # Step 6: Insert AI response into database
            ai_response_insert_data = {
                "content": full_response,
                "chat_id": chat_id,
                "clerk_id": clerk_id,
                "role": MessageRole.ASSISTANT.value,
                "citations": citations,
            }
            ai_response_creation_result = (
                supabase.table("messages").insert(ai_response_insert_data).execute()
            )
            
            if not ai_response_creation_result.data:
                logger.error("ai_response_creation_failed", chat_id=chat_id, reason="no_data_returned")  # Added: Error log
                yield f"event: error\ndata: {json.dumps({'message': 'Failed to save AI response'})}\n\n"
                return
            
            ai_message_data = ai_response_creation_result.data[0]
            logger.info("message_sent_successfully", chat_id=chat_id, ai_message_id=ai_message_data["id"])  # Added: Success log
            
            # Step 7: Send done event
            yield f"event: done\ndata: {json.dumps({'userMessage': user_message_data, 'aiMessage': ai_message_data})}\n\n"
            
        except Exception as e:
            logger.error("send_message_error", chat_id=chat_id, error=str(e), exc_info=True)  # Added: Exception log
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )