import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, List

from app.agents.dashboard_agent import (
    create_dashboard_generation_graph,
    run_dashboard_agent,
)
from app.schemas.dashboard import (
    DashboardGenerationRequest,
    DashboardGenerationResponse,
    DashboardTaskResponse,
    HumanFeedbackResponse,
)
from app.schemas.models import ModelProvider
from app.utils.llm import get_llm
from app.utils.task_store import task_store

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.post("/generate", response_model=DashboardGenerationResponse)
async def generate_dashboard(request: DashboardGenerationRequest) -> DashboardGenerationResponse:
    """
    Generate a Grafana dashboard based on the provided natural language prompt.
    """
    try:
        # Get LLM instance
        llm = get_llm(request.model_provider)
        
        # Create the workflow graph
        workflow = create_dashboard_generation_graph(
            llm=llm,
            model_provider=request.model_provider,
            use_rag=request.use_rag,
            max_retries=request.max_retries
        )
        
        # Initialize state
        initial_state = {
            "prompt": request.prompt,
            "model_provider": request.model_provider,
            "use_rag": request.use_rag,
            "max_retries": request.max_retries,
            "retry_count": 0,
            "is_valid": None,
            "error": None,
            "dashboard_json": None,
            "chat_history": [],
            "rag_context": None
        }
        
        # Run the workflow
        result = workflow.run(initial_state)
        
        # Extract results
        status = result.get("status", "failed")
        error_message = result.get("error_message")
        dashboard_json = result.get("dashboard_json")
        
        return DashboardGenerationResponse(
            status=status,
            error_message=error_message,
            dashboard_json=dashboard_json
        )
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}", exc_info=True)
        return DashboardGenerationResponse(
            status="failed",
            error_message=f"Internal server error: {str(e)}",
            dashboard_json=None
        )


@router.get("/tasks/{task_id}", response_model=DashboardTaskResponse)
async def get_task_status(task_id: str) -> DashboardTaskResponse:
    """
    Get the status of a dashboard generation task.
    """
    try:
        # Get task from memory store
        task = task_store.get(task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )
            
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/models", summary="List available LLM models")
async def list_models() -> Dict[str, List[Dict[str, str]]]:
    """
    List available LLM models.
    
    Returns:
        Dictionary of available models
    """
    return {
        "models": [
            {"id": ModelProvider.OPENAI.value, "name": "OpenAI GPT-4 Turbo"},
            {"id": ModelProvider.OPENAI4O.value, "name": "OpenAI4o (Default)"},
            {"id": ModelProvider.ANTHROPIC.value, "name": "Anthropic Claude 3 Opus"},
        ]
    }


@router.post("/{task_id}/feedback", response_model=DashboardTaskResponse)
async def submit_human_feedback(
    task_id: str, feedback: HumanFeedbackResponse
) -> DashboardTaskResponse:
    """
    Submit human feedback for a dashboard.
    
    Args:
        task_id: Unique task ID
        feedback: Human feedback response
        
    Returns:
        Updated task status
    """
    # Get task
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    
    # Check if task requires human feedback
    if (
        task.status == "completed"
        and task.result 
        and task.result.required_human_intervention
    ):
        # Update the task with human feedback
        task_store.update_task(
            task_id=task_id,
            result={
                "dashboard_json": feedback.corrected_json,
                "required_human_intervention": False,
                "human_feedback": feedback.feedback
            }
        )
        
        return task_store.get(task_id)
    else:
        raise HTTPException(
            status_code=400,
            detail="Task does not require human feedback or is not in the correct state"
        ) 