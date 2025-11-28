"""
Complete LangGraph Multi-Agent Supervisor Implementation

This module provides a complete implementation of a multi-agent supervisor system
using LangGraph. The supervisor coordinates between specialized agents (RAG and Web Search)
to handle both project-specific queries and external information retrieval.

Structure:
- State: Custom agent state with citation tracking
- Specialized Agents:
  * RAG Agent: Searches project-specific documents
  * Web Search Agent: Queries the internet for current information
- Supervisor Tools: Wrapped specialized agents as callable tools
- Supervisor Agent: Main coordinator that routes queries to appropriate agents
- System Prompts: Context-aware prompts with date information and routing logic
- Chat History: Support for conversation context across multiple turns

Key Features:
- Intelligent query routing between internal documents and web search
- Citation tracking across agent interactions
- Support for both Tavily and DuckDuckGo search engines
- Multi-agent coordination and result synthesis
- Conversation history integration for contextual understanding
"""

from typing import Any, List, Dict, Optional
from typing_extensions import Annotated
from datetime import datetime
import os

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_tavily import TavilySearch
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
    that accumulates across tool calls, allowing the supervisor and sub-agents
    to track which documents were used to answer questions.
    
    Attributes:
        citations: List of citation dictionaries that accumulate across tool calls
    """
    citations: Annotated[List[Dict[str, Any]], lambda x, y: x + y] = []


# =============================================================================
# PROMPTS
# =============================================================================

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
        User Message: What is attention?
        AI Message: Attention is a mechanism...
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


def get_supervisor_system_prompt(chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Get the system prompt for the supervisor agent, optionally including chat history.
    
    Args:
        chat_history: Optional list of previous messages with 'role' and 'content' keys.
                      If provided, the chat history will be included in the system prompt.
        
    Returns:
        The system prompt string, with chat history appended if provided
        
    Example:
        >>> # Without history
        >>> prompt = get_supervisor_system_prompt()
        
        >>> # With history
        >>> history = [{"role": "user", "content": "What is X?"}]
        >>> prompt = get_supervisor_system_prompt(chat_history=history)
    """
    current_date = datetime.now().strftime("%B %d, %Y")
    
    base_prompt = f"""You are an intelligent supervisor assistant that coordinates between two specialized agents:

**Current Date: {current_date}**

### Available Agents

1. **Project Documents Agent** (rag_search):
   - Searches internal project documents using RAG
   - Use for project-specific queries, internal documentation, uploaded files

2. **Web Search Agent** (search_web):
   - Searches the internet for current information
   - Use for current events, general knowledge, external information
   - ONLY use this tool if asked by the user or mentioned in the question

### Core Responsibilities

- Analyze user queries and determine which agent(s) to use
- Route queries to the appropriate agent(s) — you MUST NOT answer substantive questions directly
- For complex queries, coordinate multiple agents in sequence
- Synthesize results from multiple agents into coherent answers
- Prioritize project documents for project-specific questions
- Use web search ONLY if asked by the user or mentioned in the question
- Use the chat history to understand the context and references in the current question

### Query Routing Rules

**ALWAYS use tools for:**
- Any question requiring factual information
- Project-specific queries
- Technical questions
- Current events or news
- General knowledge questions
- Analysis or research requests

**Direct response permitted ONLY for:**
- Simple greetings (hi, hello, how are you)
- Acknowledgments (thanks, ok, got it)
- Basic clarification requests about your capabilities
- Farewell messages (goodbye, bye)

**ALWAYS use the RAG tool for the questions**
**Return as much information that is given from the RAG tool as possible to the user**

For all other queries, you MUST route to the appropriate agent(s) and synthesize their responses. Your role is coordination and synthesis, not direct knowledge provision.
"""
    
    if chat_history:
        formatted_history = format_chat_history(chat_history)
        if formatted_history:
            base_prompt += "\n\n### Previous Conversation Context\n"
            base_prompt += "The following is the recent conversation history for context:\n\n"
            base_prompt += formatted_history
            base_prompt += "\n\nUse this conversation history to understand context and references in the current question."
    
    return base_prompt


# =============================================================================
# RAG AGENT
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
            if not texts and not images and not tables:
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
                    "messages": [
                        ToolMessage(
                            content=response,
                            tool_call_id=tool_call_id
                        )
                    ],
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


def create_rag_agent(project_id: str, model: str = "gpt-4o"):
    """
    Create a RAG agent for searching project-specific documents.
    
    This agent is specialized for searching through internal project documents
    using RAG (Retrieval-Augmented Generation). It will be used as a sub-agent
    by the supervisor.
    
    Args:
        project_id: The UUID of the project whose documents should be searchable
        model: The OpenAI model to use (default: "gpt-4o")
        
    Returns:
        A configured LangGraph agent for RAG search
    """
    tools = [create_rag_tool(project_id)]
    
    system_prompt = """You are a helpful AI assistant with access to a RAG (Retrieval-Augmented Generation) tool that searches project-specific documents.

For every user question:

1. Do not assume any question is purely conceptual or general.  
2. Use the `rag_search` tool immediately with a clear and relevant query derived from the user's question.  
3. Carefully review the retrieved documents and base your entire answer on the RAG results.  
4. If the retrieved information fully answers the user's question, respond clearly and completely using that information.  
5. If the retrieved information is insufficient or incomplete, explicitly state that and provide helpful suggestions or guidance based on what you found.  
6. Always present answers in a clear, well-structured, and conversational manner.

**Never answer without first querying the RAG tool. This ensures every response is grounded in project-specific context and documentation.**"""
    
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=CustomAgentState
    )
    
    return agent


# =============================================================================
# WEB SEARCH AGENT
# =============================================================================

def create_web_search_agent(model: str = "gpt-4o", use_tavily: bool = True):
    """
    Create an agent with web search capabilities.
    
    This agent is specialized for searching the internet for current information.
    It supports both Tavily (paid, higher quality) and DuckDuckGo (free) as
    search backends.
    
    Args:
        model: The OpenAI model to use (default: "gpt-4o")
        use_tavily: Whether to use Tavily search (if API key available) or
                    fall back to DuckDuckGo (default: True)
        
    Returns:
        A configured LangGraph agent for web search
    """
    # Choose search tool based on availability
    if use_tavily and os.getenv("TAVILY_API_KEY"):
        search_tool = TavilySearch(max_results=5, search_depth="advanced")
    else:
        # Use DuckDuckGo as free alternative
        search_tool = DuckDuckGoSearchRun()
    
    tools = [search_tool]

    current_date = datetime.now().strftime("%B %d, %Y")
    
    system_prompt = f"""You are a specialized web search assistant.
Your job is to search the internet for current information and provide accurate, up-to-date answers.

**Current Date: {current_date}**

For every query you receive:
1. **Reformulate vague queries into specific search terms** before searching
2. Use the web search tool with clear, specific queries
3. Synthesize information from multiple search results when possible
4. Provide clear, factual answers with context
5. Indicate the recency and reliability of information when relevant

**Query Reformulation Examples:**
- "What's trending on social media today?" → Try: "Twitter trending topics today" OR "viral news today"
- "Today's top headlines" → Try: "breaking news today" OR "top news stories {current_date}"
- "What's happening in tech?" → Try: "latest tech news today" OR "technology headlines today"
- Add date context when relevant (e.g., "news {current_date}")

**If initial search returns insufficient or irrelevant results:**
1. Rephrase the query with more specific terms (e.g., add location, date, or focus area)
2. Try searching with alternative keywords or synonyms
3. Make 2-3 search attempts with different query formulations if needed
4. If still unsuccessful, clearly state what you found vs. what was requested

Focus on current events, general knowledge, and information not available in internal documents.
Never fabricate information - only use what's found in search results."""
    
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=CustomAgentState
    )
    
    return agent


# =============================================================================
# SUPERVISOR TOOLS (Wrapped Sub-Agents)
# =============================================================================

def create_supervisor_tools(project_id: str, model: str = "gpt-4o"):
    """
    Create supervisor tools that wrap the specialized agents.
    
    This function creates two tools for the supervisor:
    1. rag_search: Wraps the RAG agent for project document search
    2. search_web: Wraps the web search agent for internet queries
    
    The supervisor will use these tools to delegate work to specialized agents.
    
    Args:
        project_id: The UUID of the project for the RAG agent
        model: The OpenAI model to use for both agents (default: "gpt-4o")
        
    Returns:
        List of tools (rag_search and search_web) for the supervisor
    """
    # Create the specialized agents
    rag_agent = create_rag_agent(project_id, model)
    web_agent = create_web_search_agent(model)
    
    @tool
    def rag_search(
        query: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """Search internal project documents using RAG.
        
        Use this when the user asks about:
        - Project-specific information
        - Internal documentation
        - Previously uploaded files and documents
        - Company/project-specific data
        - Technical specifications from project files
        
        Args:
            query: Natural language query about project documents
            tool_call_id: Injected tool call ID for message tracking
            
        Returns:
            Command with relevant information from project documents and citations
        """
        result = rag_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })

        # Extract the final response
        final_message = result["messages"][-1]
        content = final_message.content if hasattr(final_message, 'content') else str(final_message)
        citations = result.get("citations", [])
        
        # Return Command that updates both messages AND citations
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=content,
                        tool_call_id=tool_call_id
                    )
                ],
                "citations": citations  # Propagate citations to supervisor state
            }
        )
    
    @tool
    def search_web(query: str) -> str:
        """Search the internet for current information.
        
        Use this when the user asks about:
        - Current events or recent news
        - General knowledge not in project documents
        - External information or public data
        - Market trends or industry news
        - Any information that requires up-to-date web sources
        
        Args:
            query: Natural language query for web search
            
        Returns:
            Relevant information from web search results
        """
        result = web_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        # Extract the final response
        final_message = result["messages"][-1]
        if hasattr(final_message, 'content'):
            return final_message.content
        return str(final_message)
    
    return [rag_search, search_web]


# =============================================================================
# SUPERVISOR AGENT CREATION
# =============================================================================

def create_supervisor_agent(
    project_id: str,
    model: str = "gpt-4o",
    chat_history: Optional[List[Dict[str, str]]] = None
):
    """
    Create a supervisor agent that coordinates RAG and web search agents.
    
    The supervisor is responsible for:
    1. Analyzing user queries to determine which agent(s) to use
    2. Routing queries to the appropriate specialized agent(s)
    3. Coordinating multiple agents for complex queries
    4. Synthesizing results from multiple agents into coherent answers
    5. Using chat history to understand context and references
    
    The supervisor has access to two tools:
    - rag_search: For searching project documents
    - search_web: For searching the internet
    
    Args:
        project_id: The UUID of the project for the RAG agent
        model: The OpenAI model to use (default: "gpt-4o")
        chat_history: Optional list of previous messages with 'role' and 'content' keys.
                     If provided, the chat history will be included in the system prompt
                     to provide conversation context.
        
    Returns:
        A configured supervisor agent that can coordinate sub-agents
        
    Example:
        >>> # Basic usage without history
        >>> supervisor = create_supervisor_agent("123e4567-e89b-12d3-a456-426614174000")
        >>> result = supervisor.invoke({
        ...     "messages": [{"role": "user", "content": "What does our documentation say about X?"}]
        ... })
        
        >>> # With chat history
        >>> history = [
        ...     {"role": "user", "content": "What is attention mechanism?"},
        ...     {"role": "assistant", "content": "Attention is a mechanism that..."}
        ... ]
        >>> supervisor = create_supervisor_agent(
        ...     project_id="123e4567-e89b-12d3-a456-426614174000",
        ...     chat_history=history
        ... )
        >>> result = supervisor.invoke({
        ...     "messages": [{"role": "user", "content": "Tell me more about it"}]
        ... })
        >>> print(result["messages"][-1].content)
        >>> print(result.get("citations", []))
    """
    # Get the supervisor tools (wrapped agents)
    tools = create_supervisor_tools(project_id, model)

    # Get the system prompt with optional chat history
    system_prompt = get_supervisor_system_prompt(chat_history=chat_history)
    
    supervisor = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=CustomAgentState
    ).with_config({"recursion_limit": 10})
    
    return supervisor