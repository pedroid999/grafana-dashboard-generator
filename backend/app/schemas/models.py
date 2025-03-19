"""
Pydantic models for the Grafana Dashboard Generator.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    OPENAI4O = "gpt-4o"  # Optimized GPT-4 configuration
    ANTHROPIC = "anthropic"


class DashboardGenerationRequest(BaseModel):
    """Request model for dashboard generation."""

    prompt: str = Field(..., description="Natural language prompt describing the dashboard")
    model_provider: ModelProvider = Field(
        default=ModelProvider.OPENAI4O, description="LLM provider to use"
    )
    max_retries: int = Field(
        default=3, description="Maximum number of retries for failed validations"
    )
    include_rag: bool = Field(
        default=True, description="Whether to use RAG for enhanced context"
    )


class ValidationError(BaseModel):
    """Model for JSON validation errors."""

    path: str = Field(..., description="JSON path where the error occurred")
    message: str = Field(..., description="Error message")


class DashboardValidationResult(BaseModel):
    """Result of dashboard JSON validation."""

    is_valid: bool = Field(..., description="Whether the JSON is valid")
    errors: List[ValidationError] = Field(
        default_factory=list, description="List of validation errors if any"
    )


class HumanFeedbackRequest(BaseModel):
    """Request for human feedback when validation fails."""

    dashboard_json: Dict[str, Any] = Field(
        ..., description="Current dashboard JSON with errors"
    )
    validation_result: DashboardValidationResult = Field(
        ..., description="Validation results showing errors"
    )
    correction_suggestions: Optional[List[str]] = Field(
        default=None, description="LLM-generated suggestions for fixing errors"
    )


class HumanFeedbackResponse(BaseModel):
    """Response from human with corrected JSON."""

    corrected_json: Dict[str, Any] = Field(
        ..., description="Corrected dashboard JSON from human"
    )
    feedback: Optional[str] = Field(
        default=None, description="Additional feedback from human reviewer"
    )


class AgentState(BaseModel):
    """State model for the LangGraph agent."""

    prompt: str = Field(..., description="Original natural language prompt")
    model_provider: ModelProvider = Field(
        ..., description="LLM provider being used"
    )
    max_retries: int = Field(..., description="Maximum retry attempts")
    current_retry: int = Field(default=0, description="Current retry attempt")
    dashboard_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Generated dashboard JSON"
    )
    validation_result: Optional[DashboardValidationResult] = Field(
        default=None, description="Results of JSON validation"
    )
    rag_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Context retrieved from RAG"
    )
    human_feedback: Optional[Dict[str, Any]] = Field(
        default=None, description="Feedback from human reviewer"
    )
    error_details: Optional[Dict[str, Any]] = Field(
        default=None, description="Details of any errors encountered"
    )


class DashboardGenerationResponse(BaseModel):
    """Response model for dashboard generation."""

    dashboard_json: Dict[str, Any] = Field(
        ..., description="Generated Grafana dashboard JSON"
    )
    validation_passed: bool = Field(
        ..., description="Whether validation passed for the generated JSON"
    )
    required_human_intervention: bool = Field(
        default=False, description="Whether human intervention was required"
    )
    retry_count: int = Field(
        default=0, description="Number of retries performed"
    ) 