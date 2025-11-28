"""
Complete LangGraph RAG Agent Implementation

This module provides a complete implementation of a RAG (Retrieval-Augmented Generation)
agent using LangGraph. The agent can search through project-specific documents and 
maintain conversation context.

Structure:
- State: Custom agent state with citation tracking
- Tools: RAG search tool for document retrieval
- Prompts: System prompts with optional chat history
- Agent: Main agent creation and configuration
"""

from typing import Any, List, Dict, Optional
from typing_extensions import Annotated

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.graph import MessagesState
from langgraph.types import Command

from src.rag.retrieval.index import retrieve_context
from src.rag.retrieval.utils import prepare_prompt_and_invoke_llm


# =============================================================================
# STATE DEFINITION
# =============================================================================

class CustomAgentState(MessagesState):
    """
    Extended agent state with citations tracking.
    
    This state extends the standard MessagesState to include a citations field
    that accumulates across tool calls, allowing the agent to track which
    documents were used to answer questions.
    
    Attributes:
        citations: List of citation dictionaries that accumulate across tool calls
    """
    # citations will accumulate across tool calls
    citations: Annotated[List[Dict[str, Any]], lambda x, y: x + y] = []


# =============================================================================
# PROMPTS
# =============================================================================

BASE_SYSTEM_PROMPT = """You are a helpful AI assistant with access to a RAG (Retrieval-Augmented Generation) tool that searches project-specific documents.

For every user question:

1. Do not assume any question is purely conceptual or general.  
2. Use the `rag_search` tool immediately with a clear and relevant query derived from the user's question. 
3. Use the chat history to understand the context and references in the current question. 
4. Carefully review the retrieved documents and base your entire answer on the RAG results.  
5. If the retrieved information fully answers the user's question, respond clearly and completely using that information.  
6. If the retrieved information is insufficient or incomplete, explicitly state that and provide helpful suggestions or guidance based on what you found.  
7. Always present answers in a clear, well-structured, and conversational manner.

**Make sure to call the rag_search tool correctly**
**Never answer without first querying the RAG tool. This ensures every response is grounded in project-specific context and documentation.**
"""


def format_chat_history(chat_history: List[Dict[str, str]]) -> str: 
    """
    Format chat history into a readable string for the system prompt.
    
    Args:
        chat_history: List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        Formatted string representation of the chat history
        
    Example:
        >>> history = [
        ...     {"role": "user", "content": "What is attention?"},
        ...     {"role": "assistant", "content": "Attention is a mechanism..."}
        ... ]
        >>> formatted = format_chat_history(history)
        >>> print(formatted)
        User: What is attention?
        Assistant: Attention is a mechanism...
    """
    if not chat_history:
        return ""
    
    formatted_messages = []
    for msg in chat_history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Format: "User Message: message" or "AI Message: message"
        role_label = "User Message" if role.lower() == "user" else "AI Message"
        formatted_messages.append(f"{role_label}: {content}")
    
    return "\n\n".join(formatted_messages)


def get_system_prompt(chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Get the system prompt for the RAG agent, optionally including chat history.
    
    Args:
        chat_history: Optional list of previous messages with 'role' and 'content' keys.
                      If provided, the chat history will be included in the system prompt.
        
    Returns:
        The system prompt string, with chat history appended if provided
        
    Example:
        >>> # Without history
        >>> prompt = get_system_prompt()
        
        >>> # With history
        >>> history = [{"role": "user", "content": "What is X?"}]
        >>> prompt = get_system_prompt(chat_history=history)
    """
    prompt = BASE_SYSTEM_PROMPT
    
    if chat_history:
        formatted_history = format_chat_history(chat_history)
        if formatted_history:
            prompt += "\n\n### Previous Conversation Context\n"
            prompt += "The following is the recent conversation history for context:\n\n"
            prompt += formatted_history
            prompt += "\n\nUse this conversation history to understand context and references in the current question."
    
    return prompt 


# =============================================================================
# TOOLS
# =============================================================================

def create_rag_tool(project_id: str):
    """
    Create a RAG search tool bound to a specific project.
    
    This factory function creates a tool that is bound to a specific project_id,
    allowing the agent to search through that project's documents.
    
    Args:
        project_id: The UUID of the project whose documents should be searchable
        
    Returns:
        A LangChain tool configured for RAG search on the specified project
        
    Example:
        >>> rag_tool = create_rag_tool("123e4567-e89b-12d3-a456-426614174000")
    """
    
    @tool
    def rag_search(
        query: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """
        Search through project documents using RAG (Retrieval-Augmented Generation).
        This tool retrieves relevant context from the current project's documents based on the query.
        
        Args:
            query: The search query or question to find relevant information
            tool_call_id: Injected tool call ID for message tracking
            
        Returns:
            A Command object with updated messages and citations
        """
        try:
            # Retrieve context using the existing RAG pipeline
            texts, images, tables, citations = retrieve_context(project_id, query)
            
            # If no context found, return a message
            if not texts:
                return Command(
                    update={
                        "messages": [
                            ToolMessage(
                                "No relevant information found in the project documents for this query.",
                                tool_call_id=tool_call_id
                            )
                        ]
                    }
                )
                
            # Prepare the response using the existing LLM preparation function
            response = prepare_prompt_and_invoke_llm(
                user_query=query,
                texts=texts,
                images=images,
                tables=tables
            )
            
            return Command(
                update={
                    # Update message history
                    "messages": [
                        ToolMessage(
                            content=response,
                            tool_call_id=tool_call_id
                        )
                    ],
                    # Update citations in state - these accumulate!
                    "citations": citations
                }
            )
            
        except Exception as e:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            f"Error retrieving information: {str(e)}",
                            tool_call_id=tool_call_id
                        )
                    ]
                }
            )

    return rag_search


# =============================================================================
# AGENT CREATION
# =============================================================================

def create_simple_rag_agent(
    project_id: str,
    model: str = "gpt-4o",
    chat_history: Optional[List[Dict[str, str]]] = None
):
    """
    Create an agent with RAG tool for a specific project.
    
    This function creates a LangGraph agent that is configured with:
    - A project-specific RAG search tool
    - Custom state schema for citation tracking
    - A system prompt that enforces RAG-first responses
    - Optional chat history context in the system prompt
    
    Args:
        project_id: The UUID of the project whose documents should be searchable
        model: The OpenAI model to use (default: "gpt-4o")
        chat_history: Optional list of previous messages with 'role' and 'content' keys.
                     If provided, the chat history will be included in the system prompt
                     to provide conversation context.
        
    Returns:
        A configured LangGraph agent that can answer questions using
        the project's documents via RAG
        
    Example:
        >>> # Basic usage without history
        >>> agent = create_rag_agent(project_id="123e4567-e89b-12d3-a456-426614174000")
        >>> result = agent.invoke({"messages": [{"role": "user", "content": "What is X?"}]})
        
        >>> # With chat history
        >>> history = [
        ...     {"role": "user", "content": "What is attention?"},
        ...     {"role": "assistant", "content": "Attention is a mechanism..."}
        ... ]
        >>> agent = create_rag_agent(
        ...     project_id="123e4567-e89b-12d3-a456-426614174000",
        ...     chat_history=history
        ... )
        >>> result = agent.invoke({"messages": [{"role": "user", "content": "Tell me more"}]})
    """
    # Create tools list with project-specific RAG tool
    tools = [create_rag_tool(project_id)]
    
    # Get the system prompt with optional chat history
    system_prompt = get_system_prompt(chat_history=chat_history)
    
    # Create the agent graph
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=CustomAgentState
    ).with_config({"recursion_limit": 5}) 
    
    return agent

