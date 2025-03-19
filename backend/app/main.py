"""
FastAPI application for Grafana Dashboard Generator.
"""

import json
import os
from typing import Any, Dict, List, Optional

import dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.agents.dashboard_agent import run_dashboard_agent
from app.schemas.models import (
    DashboardGenerationRequest,
    DashboardGenerationResponse,
    HumanFeedbackRequest,
    HumanFeedbackResponse,
    ModelProvider,
)

# Load environment variables
dotenv.load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Grafana Dashboard Generator API",
    description="API for generating Grafana dashboards using LLMs and LangGraph",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for running tasks and their results
tasks_store: Dict[str, Dict[str, Any]] = {}


class TaskResponse(BaseModel):
    """Response model for background tasks."""
    
    task_id: str = Field(..., description="Unique task ID")
    status: str = Field(..., description="Task status (pending, completed, failed)")


class TaskStatusResponse(TaskResponse):
    """Response model for task status."""
    
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Result if task is completed"
    )


def generate_task_id() -> str:
    """Generate a unique task ID."""
    import uuid
    
    return str(uuid.uuid4())


async def run_dashboard_generation_task(
    task_id: str, request: DashboardGenerationRequest
) -> None:
    """
    Run the dashboard generation task in the background.
    
    Args:
        task_id: Unique task ID
        request: Dashboard generation request
    """
    try:
        # Set task as pending
        tasks_store[task_id] = {"status": "pending"}
        
        # Run the dashboard agent
        result = run_dashboard_agent(
            prompt=request.prompt,
            model_provider=request.model_provider,
            max_retries=request.max_retries,
        )
        
        # Update task store
        tasks_store[task_id] = {
            "status": "completed",
            "result": {
                "dashboard_json": result["dashboard_json"],
                "validation_passed": result["validation_passed"],
                "required_human_intervention": result["required_human_intervention"],
                "retry_count": result["retry_count"],
            },
        }
    except Exception as e:
        # Update task store with error
        tasks_store[task_id] = {
            "status": "failed",
            "error": str(e),
        }


@app.post(
    "/api/dashboards/generate", 
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate a Grafana dashboard",
    description="Start a dashboard generation task based on the provided prompt and model settings",
)
async def generate_dashboard(
    request: DashboardGenerationRequest, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Generate a Grafana dashboard based on a natural language prompt.
    
    Args:
        request: Dashboard generation request
        background_tasks: FastAPI background tasks
        
    Returns:
        Task ID and status
    """
    # Generate task ID
    task_id = generate_task_id()
    
    # Start background task
    background_tasks.add_task(run_dashboard_generation_task, task_id, request)
    
    return {
        "task_id": task_id,
        "status": "pending",
    }


@app.get(
    "/api/tasks/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get task status",
    description="Get the status of a running or completed task",
)
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a task.
    
    Args:
        task_id: Unique task ID
        
    Returns:
        Task status and result if completed
    """
    if task_id not in tasks_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    task_info = tasks_store[task_id]
    response = {
        "task_id": task_id,
        "status": task_info["status"],
    }
    
    if task_info["status"] == "completed" and "result" in task_info:
        response["result"] = task_info["result"]
    elif task_info["status"] == "failed" and "error" in task_info:
        response["error"] = task_info["error"]
    
    return response


@app.post(
    "/api/tasks/{task_id}/feedback",
    response_model=TaskStatusResponse,
    summary="Provide human feedback",
    description="Submit human feedback for a dashboard that required intervention",
)
async def submit_human_feedback(
    task_id: str, feedback: HumanFeedbackResponse
) -> Dict[str, Any]:
    """
    Submit human feedback for a dashboard.
    
    Args:
        task_id: Unique task ID
        feedback: Human feedback response
        
    Returns:
        Updated task status
    """
    if task_id not in tasks_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    task_info = tasks_store[task_id]
    
    # Check if task requires human feedback
    if (
        task_info["status"] == "completed"
        and "result" in task_info
        and task_info["result"].get("required_human_intervention", False)
    ):
        # Update the task with human feedback
        task_info["result"]["dashboard_json"] = feedback.corrected_json
        task_info["result"]["human_feedback"] = feedback.feedback
        task_info["result"]["validation_passed"] = True  # Assume human-corrected JSON is valid
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": task_info["result"],
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task does not require human feedback or is not in the correct state",
        )


@app.get(
    "/api/models",
    summary="List available LLM models",
    description="Get a list of available LLM providers/models",
)
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


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    
    # Start the FastAPI app with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 