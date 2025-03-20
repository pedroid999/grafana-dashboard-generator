"""
FastAPI application for Grafana Dashboard Generator.
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional

import dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.dashboard_agent import run_dashboard_agent
from app.schemas.models import (
    ModelProvider,
)
from app.schemas.dashboard import (
    DashboardGenerationRequest,
    DashboardGenerationResponse,
    DashboardTaskResponse,
)
from app.utils.task_store import task_store

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("app.main")

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

# Include routers - Make sure these are registered correctly
from app.routes import dashboard
app.include_router(dashboard.router, prefix="/api")


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
        logger.info(f"Task {task_id} starting - model: {request.model_provider}, prompt: {request.prompt}")
        
        # Run the dashboard agent
        logger.debug(f"Calling dashboard agent with params: {request}")
        result = run_dashboard_agent(
            prompt=request.prompt,
            model_provider=request.model_provider,
            max_retries=request.max_retries,
            use_rag=request.use_rag,
        )
        
        logger.info(f"Task {task_id} completed with status: {result.get('status', 'unknown')}")
        logger.debug(f"Result: {result}")
        
        # Update task store with result
        task_store.update_task(
            task_id=task_id,
            status=result.get("status", "failed"),
            error=result.get("error_message"),
            result={
                "dashboard_json": result.get("dashboard_json"),
                "retry_count": result.get("retry_count", 0),
                "required_human_intervention": False,  # Default to false
            }
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Task {task_id} failed with error: {str(e)}")
        logger.error(f"Error details: {error_details}")
        
        # Update task store with error
        task_store.update_task(
            task_id=task_id,
            status="failed",
            error=f"Internal error: {str(e)}. Details: {error_details[:500]}"
        )


@app.post(
    "/api/dashboards/generate", 
    response_model=DashboardTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate a Grafana dashboard",
    description="Start a dashboard generation task based on the provided prompt and model settings",
)
async def generate_dashboard(
    request: DashboardGenerationRequest, background_tasks: BackgroundTasks
) -> DashboardTaskResponse:
    """
    Generate a Grafana dashboard based on a natural language prompt.
    
    Args:
        request: Dashboard generation request
        background_tasks: FastAPI background tasks
        
    Returns:
        Task ID and status
    """
    # Create new task
    task_id = task_store.create_task()
    
    # Start background task
    background_tasks.add_task(run_dashboard_generation_task, task_id, request)
    
    # Return task info
    return task_store.get(task_id)


@app.get("/api/tasks/{task_id}", response_model=DashboardTaskResponse)
async def get_task_status(task_id: str) -> DashboardTaskResponse:
    """
    Get the status of a dashboard generation task.
    
    Args:
        task_id: Unique task ID
        
    Returns:
        Task status
    """
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    return task


@app.get("/api/models")
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
            {"id": ModelProvider.OPENAI_O3_MINI.value, "name": "OpenAI o3-mini"},
            {"id": ModelProvider.ANTHROPIC.value, "name": "Anthropic Claude 3 Opus"},
        ]
    }


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Status message
    """
    return {"status": "ok"} 