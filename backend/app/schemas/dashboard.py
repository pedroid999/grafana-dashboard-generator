from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.schemas.models import ModelProvider


class DashboardGenerationRequest(BaseModel):
    """Request model for dashboard generation."""
    prompt: str = Field(..., description="Natural language prompt describing the desired dashboard")
    model_provider: ModelProvider = Field(
        default=ModelProvider.OPENAI4O,
        description="The LLM provider to use for generation"
    )
    use_rag: bool = Field(
        default=False,
        description="Whether to use RAG for enhanced generation"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for validation"
    )


class DashboardGenerationResponse(BaseModel):
    """Response model for dashboard generation."""
    status: str = Field(..., description="Status of the generation task")
    error_message: Optional[str] = Field(
        None,
        description="Error message if generation failed"
    )
    dashboard_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Generated dashboard JSON if successful"
    )


class DashboardValidationResult(BaseModel):
    """Result of dashboard JSON validation."""
    is_valid: bool = Field(..., description="Whether the dashboard JSON is valid")
    error: Optional[str] = Field(
        None,
        description="Error message if validation failed"
    )


class TaskResult(BaseModel):
    """Result of a dashboard generation task."""
    dashboard_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Generated dashboard JSON"
    )
    retry_count: Optional[int] = Field(
        None,
        description="Number of retries performed"
    )
    required_human_intervention: Optional[bool] = Field(
        None,
        description="Whether human intervention is required"
    )


class DashboardTaskResponse(BaseModel):
    """Response model for task status."""
    task_id: str = Field(..., description="The ID of the task")
    status: str = Field(..., description="Status of the task (pending, completed, failed)")
    error: Optional[str] = Field(
        None,
        description="Error message if task failed"
    )
    result: Optional[TaskResult] = Field(
        None,
        description="Task result if completed"
    )


class HumanFeedbackResponse(BaseModel):
    """Response model for human feedback."""
    corrected_json: Dict[str, Any] = Field(
        ...,
        description="Corrected dashboard JSON"
    )
    feedback: str = Field(
        "",
        description="Optional feedback message"
    ) 