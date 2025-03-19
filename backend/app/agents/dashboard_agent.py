"""
LangGraph agent for Grafana dashboard generation.
"""

import json
from typing import Any, Annotated, Dict, List, Optional, TypedDict

import langgraph.graph as lg
from langgraph import graph
from langgraph.checkpoint import Checkpoint
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
    rag_context = get_rag_context(state.prompt)
    state.rag_context = rag_context
    return state


def generate_dashboard_json(state: AgentState) -> AgentState:
    """
    Generate dashboard JSON using the specified LLM.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with generated dashboard JSON
    """
    llm = get_llm(state.model_provider)
    chain = create_dashboard_generator_chain(llm)
    
    # If we have RAG context, include it in the prompt
    if state.rag_context:
        formatted_context = format_rag_context_as_text(state.rag_context)
        prompt = RAG_AUGMENTED_PROMPT.format(
            user_prompt=state.prompt, rag_context=formatted_context
        )
    else:
        prompt = state.prompt
    
    # Try to generate valid JSON
    try:
        response = chain.invoke({"prompt": prompt, "chat_history": []})
        # Extract JSON from potential text
        dashboard_str = response.content
        # Remove markdown code blocks if present
        if dashboard_str.startswith("```json"):
            dashboard_str = dashboard_str.split("```json")[1]
        if dashboard_str.startswith("```"):
            dashboard_str = dashboard_str.split("```")[1]
        if dashboard_str.endswith("```"):
            dashboard_str = dashboard_str.rsplit("```", 1)[0]
        
        # Parse the result as JSON
        dashboard_json = json.loads(dashboard_str.strip())
        state.dashboard_json = dashboard_json
    except Exception as e:
        state.error_details = {
            "stage": "generation",
            "error": str(e),
            "message": "Failed to generate valid JSON",
        }
    
    return state


def validate_json(state: AgentState) -> AgentState:
    """
    Validate the generated dashboard JSON.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with validation results
    """
    if not state.dashboard_json:
        state.validation_result = DashboardValidationResult(is_valid=False, errors=[])
        return state
    
    validation_result = validate_dashboard_json(state.dashboard_json)
    state.validation_result = validation_result
    
    return state


def fix_json(state: AgentState) -> AgentState:
    """
    Fix validation errors in the dashboard JSON.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with fixed dashboard JSON
    """
    # Increment retry counter
    state.current_retry += 1
    
    # If we've exceeded max retries, don't attempt another fix
    if state.current_retry > state.max_retries:
        state.error_details = {
            "stage": "fix",
            "error": "Max retries exceeded",
            "message": "Failed to fix JSON after maximum retry attempts",
        }
        return state
    
    if not state.validation_result or not state.dashboard_json:
        return state
    
    # Extract error patterns for better context
    error_patterns = extract_error_patterns(state.validation_result)
    
    llm = get_llm(state.model_provider)
    fix_chain = create_dashboard_fix_chain(llm)
    
    try:
        # Format the dashboard JSON for the prompt
        dashboard_str = json.dumps(state.dashboard_json, indent=2)
        
        # Invoke the fix chain
        response = fix_chain.invoke({
            "dashboard_json": dashboard_str,
            "error_patterns": "\n".join(error_patterns)
        })
        
        # Extract JSON from the response
        fixed_json_str = response.content
        # Remove markdown code blocks if present
        if fixed_json_str.startswith("```json"):
            fixed_json_str = fixed_json_str.split("```json")[1]
        if fixed_json_str.startswith("```"):
            fixed_json_str = fixed_json_str.split("```")[1]
        if fixed_json_str.endswith("```"):
            fixed_json_str = fixed_json_str.rsplit("```", 1)[0]
        
        # Parse the fixed JSON
        fixed_json = json.loads(fixed_json_str.strip())
        state.dashboard_json = fixed_json
    except Exception as e:
        state.error_details = {
            "stage": "fix",
            "error": str(e),
            "message": "Failed to fix dashboard JSON",
        }
    
    return state


def human_in_loop(state: AgentState) -> AgentState:
    """
    Pause execution for human intervention.
    
    In a real system, this would interact with an API to get human feedback.
    For this demo, we'll simulate by setting a flag in the state.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with human feedback flag
    """
    # Mark the state as requiring human intervention
    state.human_feedback = {
        "required": True,
        "message": "Validation errors persist after automatic fixing attempts",
        "dashboard_json": state.dashboard_json,
        "validation_result": state.validation_result,
    }
    
    return state


def should_retry(state: AgentState) -> bool:
    """
    Determine if the agent should retry JSON generation/fixing.
    
    Args:
        state: Current agent state
        
    Returns:
        True if retry is needed, False otherwise
    """
    # If validation succeeded, no need to retry
    if state.validation_result and state.validation_result.is_valid:
        return False
    
    # If we've exceeded max retries, don't retry
    if state.current_retry >= state.max_retries:
        return False
    
    # If there are no errors to fix, don't retry
    if not state.dashboard_json or not state.validation_result:
        return False
    
    return True


def should_ask_human(state: AgentState) -> bool:
    """
    Determine if human intervention is needed.
    
    Args:
        state: Current agent state
        
    Returns:
        True if human intervention is needed, False otherwise
    """
    # If validation passed, no need for human intervention
    if state.validation_result and state.validation_result.is_valid:
        return False
    
    # If we've exceeded max retries and validation still fails, ask human
    if state.current_retry >= state.max_retries and state.validation_result and not state.validation_result.is_valid:
        return True
    
    return False


def finalize(state: AgentState) -> AgentState:
    """
    Finalize the agent execution and prepare the response.
    
    Args:
        state: Current agent state
        
    Returns:
        The final agent state
    """
    # No changes needed, just return the state
    return state


def create_dashboard_generation_graph() -> lg.Graph:
    """
    Create the LangGraph for dashboard generation.
    
    Returns:
        A configured LangGraph instance
    """
    # Define the graph
    workflow = lg.Graph()
    
    # Add nodes to the graph
    workflow.add_node("add_rag_context", add_rag_context)
    workflow.add_node("generate_dashboard_json", generate_dashboard_json)
    workflow.add_node("validate_json", validate_json)
    workflow.add_node("fix_json", fix_json)
    workflow.add_node("human_in_loop", human_in_loop)
    workflow.add_node("finalize", finalize)
    
    # Add edges to define the flow
    workflow.add_edge("add_rag_context", "generate_dashboard_json")
    workflow.add_edge("generate_dashboard_json", "validate_json")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "validate_json",
        # If validation fails and we should retry, go to fix_json
        # If validation fails and we should ask human, go to human_in_loop
        # Otherwise, go to finalize
        {
            should_retry: "fix_json",
            should_ask_human: "human_in_loop",
            lambda state: True: "finalize"  # Default case
        }
    )
    
    workflow.add_edge("fix_json", "validate_json")  # After fixing, revalidate
    workflow.add_edge("human_in_loop", "finalize")  # After human intervention, finalize
    
    # Set the entry point
    workflow.set_entry_point("add_rag_context")
    
    return workflow


def run_dashboard_agent(
    prompt: str,
    model_provider: ModelProvider = ModelProvider.OPENAI4O,
    max_retries: int = 3,
    checkpoint: Optional[Checkpoint] = None,
) -> Dict[str, Any]:
    """
    Run the dashboard generation agent.
    
    Args:
        prompt: The user's natural language prompt
        model_provider: LLM provider to use
        max_retries: Maximum retries for validation failures
        checkpoint: Optional checkpoint to resume from
        
    Returns:
        Dict with the final state and dashboard JSON
    """
    # Initialize state
    initial_state = initialize_state(
        prompt=prompt,
        model_provider=model_provider,
        max_retries=max_retries,
    )
    
    # Create graph
    workflow = create_dashboard_generation_graph()
    
    # Compile the graph into a runnable
    app = workflow.compile()
    
    # Run the graph
    if checkpoint:
        # Resume from checkpoint
        result = app.continue_from_checkpoint(checkpoint)
    else:
        # Start new run
        result = app.invoke(initial_state)
    
    # Return the final state
    return {
        "state": result,
        "dashboard_json": result.dashboard_json,
        "validation_passed": result.validation_result.is_valid if result.validation_result else False,
        "required_human_intervention": bool(result.human_feedback and result.human_feedback.get("required", False)),
        "retry_count": result.current_retry,
    } 