/**
 * Types for dashboard-related entities
 */

export type ModelProvider = 'openai' | 'anthropic' | 'gpt-4o' | 'o3-mini';

export interface DashboardGenerationRequest {
  prompt: string;
  model_provider: ModelProvider;
  max_retries?: number;
  use_rag?: boolean;
}

export interface ValidationError {
  path: string;
  message: string;
}

export interface DashboardValidationResult {
  is_valid: boolean;
  errors: ValidationError[];
}

export interface HumanFeedbackRequest {
  dashboard_json: Record<string, unknown>;
  validation_result: DashboardValidationResult;
  correction_suggestions?: string[];
}

export interface HumanFeedbackResponse {
  corrected_json: Record<string, unknown>;
  feedback?: string;
}

export interface TaskResponse {
  task_id: string;
  status: 'pending' | 'completed' | 'failed';
  result?: {
    dashboard_json: Record<string, unknown>;
    validation_passed: boolean;
    required_human_intervention: boolean;
    retry_count: number;
  };
  error?: string;
}

export interface ModelInfo {
  id: ModelProvider;
  name: string;
} 