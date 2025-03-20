"""
LangGraph agent for Grafana dashboard generation.
"""

import json
import logging
import re
from typing import Any, Annotated, Dict, List, Optional, TypedDict

from langgraph.graph import Graph
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.rag.retriever import format_rag_context_as_text, get_rag_context
from app.schemas.grafana_schema import (
    extract_error_patterns,
    validate_dashboard_json,
)
from app.schemas.models import (
    AgentState,
    DashboardValidationResult,
    ModelProvider,
)
from app.utils.llm import (
    RAG_AUGMENTED_PROMPT,
    create_dashboard_fix_chain,
    create_dashboard_generator_chain,
    get_llm,
)

# Add debugger import
import pdb

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Function definitions for state management 

def is_valid_dashboard(state: Dict[str, Any]) -> bool:
    """Check if the dashboard is valid."""
    return state.get("is_valid", False) is True


def should_retry(state: Dict[str, Any]) -> bool:
    """Check if we should retry fixing the dashboard."""
    is_valid = state.get("is_valid")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    # Not valid and still have retries left
    return is_valid is False and retry_count < max_retries


def should_end(state: Dict[str, Any]) -> bool:
    """Check if we should end the generation process."""
    is_valid = state.get("is_valid")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    # Not valid and used up all retries
    return is_valid is False and retry_count >= max_retries

# State initialization

def initialize_state(
    prompt: str, model_provider: ModelProvider, max_retries: int = 3
) -> AgentState:
    """
    Initialize the agent state.
    
    Args:
        prompt: The user's prompt for dashboard generation
        model_provider: The LLM provider to use
        max_retries: Maximum number of retries for validation failures
        
    Returns:
        Initialized AgentState object
    """
    # DEBUGGING PUNTO 1: Inicialización del estado del agente
    return AgentState(
        prompt=prompt,
        model_provider=model_provider,
        max_retries=max_retries,
        current_retry=0,
    )


def add_rag_context(state: AgentState) -> AgentState:
    """
    Add RAG context to the agent state.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with RAG context
    """
    from app.rag.retriever import get_rag_context, format_rag_context_as_text
    
    # Retrieve raw context based on the prompt
    raw_context = get_rag_context(state.prompt)
    
    # Format the context as readable text for the prompt
    formatted_context = format_rag_context_as_text(raw_context)
    
    # Store both raw and formatted context in the state
    state.rag_context = {
        "raw": raw_context,
        "formatted": formatted_context
    }
    
    return state

# Core graph node functions

def generate_dashboard_json(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a Grafana dashboard JSON based on the user's prompt.
    
    Args:
        state: Current state containing the user's prompt and configuration
        
    Returns:
        Updated state with generated dashboard JSON
    """
    try:
        prompt = state.get("prompt")
        if not prompt:
            return {
                **state,
                "is_valid": False,
                "error": "No prompt provided"
            }
            
        # Get the LLM instance
        llm = get_llm(state.get("model_provider", ModelProvider.OPENAI4O))
        
        # Create the generation chain
        generation_chain = create_dashboard_generator_chain(llm)
        
        # Prepare the context
        context = {
            "prompt": prompt,
            "chat_history": state.get("chat_history", [])
        }
        
        if state.get("use_rag"):
            rag_context = state.get("rag_context", {})
            formatted_context = rag_context.get("formatted", "") if isinstance(rag_context, dict) else ""
            context["prompt"] = RAG_AUGMENTED_PROMPT.format(
                user_prompt=prompt,
                rag_context=formatted_context
            )
        
        # Generate the dashboard JSON
        logger.debug(f"Invoking generation chain with context: {str(context)[:200]}...")
        
        try:
            response = generation_chain.invoke(context)
            logger.debug(f"Response type: {type(response)}")
        except Exception as chain_error:
            logger.error(f"Error in generation chain: {str(chain_error)}")
            # Si quieres hacer un debug interactivo, descomenta la siguiente línea
            # pdb.set_trace()
            raise ValueError(f"Generation chain error: {str(chain_error)}")
        
        # Parse the response
        try:
            # Check if response is an AIMessage or similar LLM response object
            if hasattr(response, "content"):
                response_text = response.content
            else:
                response_text = str(response)
                
            # Log the response for debugging
            logger.debug(f"Raw LLM response: {response_text[:200]}...")
            
            # Try to parse as JSON
            try:
                dashboard_json = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON if wrapped in markdown
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    dashboard_json = json.loads(json_match.group(1))
                else:
                    raise ValueError("Could not parse JSON from response")
            
            return {
                **state,
                "dashboard_json": dashboard_json,
                "is_valid": None  # Will be determined by validation
            }
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            logger.error(f"Response type: {type(response)}")
            logger.error(f"Response content: {str(response)[:500]}")
            raise ValueError(f"Failed to parse dashboard JSON: {str(e)}")
        
    except Exception as e:
        return {
            **state,
            "is_valid": False,
            "error": f"Generation error: {str(e)}"
        }


def validate_dashboard_json(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the generated dashboard JSON.
    
    Args:
        state: Current state containing the dashboard JSON
        
    Returns:
        Updated state with validation results
    """
    try:
        dashboard_json = state.get("dashboard_json")
        if not dashboard_json:
            return {
                **state,
                "is_valid": False,
                "error": "No dashboard JSON found in state"
            }
            
        # Validate required fields
        required_fields = ["title", "panels"]
        missing_fields = [field for field in required_fields if field not in dashboard_json]
        
        if missing_fields:
            return {
                **state,
                "is_valid": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }
            
        # Validate panels
        panels = dashboard_json.get("panels", [])
        for panel in panels:
            if not isinstance(panel, dict):
                return {
                    **state,
                    "is_valid": False,
                    "error": "Invalid panel format"
                }
                
            # Check required panel fields
            required_panel_fields = ["id", "type", "title", "gridPos"]
            missing_panel_fields = [
                field for field in required_panel_fields 
                if field not in panel
            ]
            
            if missing_panel_fields:
                return {
                    **state,
                    "is_valid": False,
                    "error": f"Panel missing required fields: {', '.join(missing_panel_fields)}"
                }
                
            # Validate gridPos
            grid_pos = panel.get("gridPos", {})
            required_grid_fields = ["h", "w", "x", "y"]
            missing_grid_fields = [
                field for field in required_grid_fields 
                if field not in grid_pos
            ]
            
            if missing_grid_fields:
                return {
                    **state,
                    "is_valid": False,
                    "error": f"GridPos missing required fields: {', '.join(missing_grid_fields)}"
                }
        
        # If we get here, validation passed
        return {
            **state,
            "is_valid": True,
            "error": None
        }
        
    except Exception as e:
        return {
            **state,
            "is_valid": False,
            "error": f"Validation error: {str(e)}"
        }


def end_generation(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    End the generation process and return final state.
    
    Args:
        state: Current state
        
    Returns:
        Final state with status
    """
    is_valid = state.get("is_valid", False)
    error = state.get("error")
    
    return {
        **state,
        "status": "completed" if is_valid else "failed",
        "error_message": error if error else None
    }


def fix_dashboard_json(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix validation errors in the dashboard JSON.
    
    Args:
        state: Current state containing the dashboard JSON and error information
        
    Returns:
        Updated state with fixed dashboard JSON
    """
    try:
        dashboard_json = state.get("dashboard_json")
        error = state.get("error")
        
        if not dashboard_json or not error:
            logger.warning("Missing dashboard JSON or error information in fix_dashboard_json")
            return {
                **state,
                "is_valid": False,
                "error": "Missing dashboard JSON or error information",
                "status": "failed",  # Mark as failed to break the loop
                "error_message": "Missing dashboard JSON or error information"
            }
            
        # Get the current retry count and max retries
        retry_count = state.get("retry_count", 0) 
        max_retries = state.get("max_retries", 3)
        
        # Safety check - don't retry more than max_retries
        if retry_count >= max_retries:
            logger.warning(f"Max retries ({max_retries}) reached in fix_dashboard_json")
            return {
                **state,
                "is_valid": False,
                "error": f"Failed to fix dashboard after {retry_count} attempts",
                "status": "failed",
                "error_message": f"Failed to fix dashboard after {retry_count} attempts"
            }
            
        # Update retry count immediately to ensure we don't loop forever
        retry_count += 1
        logger.info(f"Fix attempt {retry_count}/{max_retries} starting")
            
        # Get the LLM instance
        llm = get_llm(state.get("model_provider", ModelProvider.OPENAI4O))
        
        # Create the fix chain
        fix_chain = create_dashboard_fix_chain(llm)
        
        # Prepare input for the chain
        json_str = json.dumps(dashboard_json, indent=2) if isinstance(dashboard_json, dict) else str(dashboard_json)
        
        # Run the chain
        logger.debug(f"Sending error for fixing: {error[:100]}...")
        
        try:
            response = fix_chain.invoke({
                "dashboard_json": json_str,
                "error_patterns": error
            })
            logger.debug(f"Fix chain response type: {type(response)}")
        except Exception as chain_error:
            logger.error(f"Error in fix chain: {str(chain_error)}")
            # Si quieres hacer un debug interactivo, descomenta la siguiente línea
            # pdb.set_trace()
            raise ValueError(f"Fix chain error: {str(chain_error)}")
        
        # Parse the response
        try:
            # Log the raw response for debugging
            logger.debug(f"Raw response from fix chain: {str(response)[:200]}...")
            
            # Extract content from AIMessage if needed
            if hasattr(response, "content"):
                response_text = response.content
            else:
                response_text = str(response)
                
            # Try to extract JSON if wrapped in markdown
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                fixed_json_str = json_match.group(1)
                logger.debug(f"Extracted JSON from markdown: {fixed_json_str[:100]}...")
                fixed_json = json.loads(fixed_json_str)
            else:
                # Try direct JSON parsing
                fixed_json = json.loads(response_text)
        except Exception as json_error:
            logger.error(f"Failed to parse fixed JSON: {str(json_error)}")
            if retry_count >= max_retries:
                logger.error(f"Failed on final retry ({retry_count}/{max_retries})")
                return {
                    **state,
                    "is_valid": False,
                    "error": f"Failed to parse fixed JSON: {str(json_error)}",
                    "status": "failed",
                    "error_message": f"Failed to parse fixed JSON: {str(json_error)}",
                    "retry_count": retry_count
                }
            else:
                # Return with current retry count but no state change
                return {
                    **state,
                    "retry_count": retry_count,
                    "is_valid": False,
                    "error": f"Parsing error in fix attempt {retry_count}: {str(json_error)}"
                }
        
        # Log the fix attempt
        logger.info(f"Fix attempt {retry_count}/{max_retries} completed")
        
        return {
            **state,
            "dashboard_json": fixed_json,
            "retry_count": retry_count,
            "is_valid": None  # Will be determined by next validation
        }
        
    except Exception as e:
        logger.error(f"Error in fix_dashboard_json: {str(e)}")
        
        # Return error state to break the loop
        return {
            **state,
            "is_valid": False,
            "error": f"Fix error: {str(e)}",
            "status": "failed",  # Mark as failed to break the loop
            "error_message": f"Fix error: {str(e)}",
            "retry_count": state.get("retry_count", 0) + 1  # Increment retry count to avoid infinite loops
        }

# RAG functions

def retrieve_similar_dashboards(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve similar dashboards for RAG context.
    
    Args:
        state: Current state with user prompt
        
    Returns:
        Updated state with retrieved dashboards
    """
    try:
        prompt = state.get("prompt")
        if not prompt:
            return {
                **state,
                "rag_context": None,
                "error": "No prompt provided for retrieval"
            }
            
        # Retrieve similar dashboards
        rag_context = get_rag_context(prompt)
        
        return {
            **state,
            "rag_context": rag_context
        }
    except Exception as e:
        return {
            **state,
            "rag_context": None,
            "error": f"Retrieval error: {str(e)}"
        }


def enhance_with_rag(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance the prompt with RAG context.
    
    Args:
        state: Current state with rag context
        
    Returns:
        Updated state with enhanced prompt
    """
    try:
        prompt = state.get("prompt")
        rag_context = state.get("rag_context", {})
        
        if not prompt:
            return {
                **state,
                "error": "No prompt provided for enhancement"
            }
            
        if not rag_context:
            # No RAG context, just proceed with original prompt
            return state
        
        # Get formatted context if available, or format it if not
        if isinstance(rag_context, dict):
            formatted_context = rag_context.get("formatted", "")
            if not formatted_context and "raw" in rag_context:
                # If we have raw but not formatted, format it now
                from app.rag.retriever import format_rag_context_as_text
                formatted_context = format_rag_context_as_text(rag_context["raw"])
        else:
            # Legacy context object, use as is
            from app.rag.retriever import format_rag_context_as_text
            formatted_context = format_rag_context_as_text(rag_context)
            
        # Enhance the prompt
        enhanced_prompt = RAG_AUGMENTED_PROMPT.format(
            user_prompt=prompt,
            rag_context=formatted_context
        )
        
        return {
            **state,
            "enhanced_prompt": enhanced_prompt
        }
    except Exception as e:
        return {
            **state,
            "error": f"Enhancement error: {str(e)}"
        }

# Graph creation

def create_dashboard_generation_graph(
    llm: BaseChatModel,
    model_provider: ModelProvider,
    use_rag: bool = False,
    max_retries: int = 3,
) -> Graph:
    """
    Create the graph for dashboard generation workflow.
    
    Args:
        llm: The LLM to use for generation
        model_provider: The model provider to use
        use_rag: Whether to use RAG for enhanced generation
        max_retries: Maximum number of retries for validation
        
    Returns:
        The workflow graph
    """
    # Create the nodes
    nodes = {
        "generate": generate_dashboard_json,
        "validate": validate_dashboard_json,
        "fix": fix_dashboard_json,
        "end": end_generation,
    }
    
    if use_rag:
        nodes["retrieve"] = retrieve_similar_dashboards
        nodes["enhance"] = enhance_with_rag
    
    # Create the graph, without recursion_limit (not supported in this version)
    workflow = Graph()
    
    # Add nodes to the graph
    for node_name, node_func in nodes.items():
        workflow.add_node(node_name, node_func)
    
    # Set entry point based on RAG configuration
    if use_rag:
        # If using RAG, start with retrieve
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "enhance")
        workflow.add_edge("enhance", "generate")
    else:
        # If not using RAG, start with generate
        workflow.set_entry_point("generate")
    
    # Add common edges
    workflow.add_edge("generate", "validate")
    
    # Define conditional edges correctly with better handling to avoid infinite loops
    def route_to_end(state):
        # Safety check - make sure we're not in an infinite loop
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        # Log the current state for debugging
        logger.debug(f"route_to_end: is_valid={state.get('is_valid')}, retry_count={retry_count}, max_retries={max_retries}")
        
        # If dashboard is valid, go to end
        if is_valid_dashboard(state):
            logger.debug("Decision: end (dashboard is valid)")
            return "end"
            
        # If we've hit retry limit, go to end
        if retry_count >= max_retries:
            logger.debug("Decision: end (retry limit reached)")
            return "end"
            
        # Otherwise try to fix it
        logger.debug("Decision: fix (needs correction)")
        return "fix"
    
    # Add a single conditional routing function
    workflow.add_conditional_edges(
        "validate",
        route_to_end
    )
    
    # Add the remaining edge
    workflow.add_edge("fix", "validate")
    
    return workflow

# Main execution function

def run_dashboard_agent(
    prompt: str,
    model_provider: ModelProvider = ModelProvider.OPENAI4O,
    max_retries: int = 3,
    use_rag: bool = True,
) -> Dict[str, Any]:
    """
    Run the dashboard generation agent.
    
    Args:
        prompt: Natural language prompt describing the dashboard
        model_provider: LLM provider to use
        max_retries: Maximum number of retry attempts
        use_rag: Whether to use RAG for enhanced generation
        
    Returns:
        Generated dashboard JSON and status
    """
    logger.info(f"Starting dashboard generation with model: {model_provider}")
    logger.info(f"Prompt: {prompt}")
    
    try:
        # Get LLM instance
        logger.debug("Getting LLM instance")
        llm = get_llm(model_provider)
        
        # Create workflow graph
        logger.debug(f"Creating workflow graph with use_rag={use_rag}, max_retries={max_retries}")
        workflow = create_dashboard_generation_graph(
            llm=llm,
            model_provider=model_provider,
            use_rag=use_rag,
            max_retries=max_retries
        )
        
        # Initialize state
        logger.debug("Initializing state")
        initial_state = {
            "prompt": prompt,
            "model_provider": model_provider,
            "use_rag": use_rag,
            "max_retries": max_retries,
            "retry_count": 0,
            "is_valid": None,
            "error": None,
            "dashboard_json": None,
            "chat_history": [],
            "rag_context": None
        }
        
        # Run the workflow
        logger.debug("Compiling and running workflow")
        app = workflow.compile()
        
        try:
            # Standard execution with LangGraph
            final_state = app.invoke(initial_state)
            logger.debug(f"Workflow completed. Final state keys: {list(final_state.keys())}")
            
            # Extract results
            status = final_state.get("status", "failed")
            error_message = final_state.get("error_message") or final_state.get("error")
            dashboard_json = final_state.get("dashboard_json")
            
            logger.info(f"Dashboard generation completed with status: {status}")
            if error_message:
                logger.warning(f"Error message: {error_message}")
            
            return {
                "status": status,
                "error_message": error_message,
                "dashboard_json": dashboard_json,
                "retry_count": final_state.get("retry_count", 0)
            }
        except Exception as graph_error:
            # Handle recursion limit or other graph execution errors
            logger.error(f"Graph execution error: {str(graph_error)}")
            
            # Check if it's a recursion error
            if "recursion" in str(graph_error).lower():
                error_msg = "Maximum recursion depth exceeded. The graph went into an infinite loop."
            else:
                error_msg = f"Workflow error: {str(graph_error)}"
            
            return {
                "status": "failed",
                "error_message": error_msg,
                "dashboard_json": initial_state.get("dashboard_json"),
                "retry_count": initial_state.get("retry_count", 0)
            }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error executing dashboard agent: {str(e)}")
        logger.error(f"Error details: {error_details}")
        
        return {
            "status": "failed",
            "error_message": f"Internal error: {str(e)}",
            "error_details": error_details[:1000],  # Include truncated stack trace
            "dashboard_json": None,
            "retry_count": 0
        } 