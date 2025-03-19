/**
 * Types for dashboard-related entities
 */

export type ModelProvider = 'openai' | 'anthropic' | 'openai4o';

export interface DashboardGenerationRequest {
  prompt: string;
  model_provider: ModelProvider;
  max_retries?: number;
  include_rag?: boolean;
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
  dashboard_json: Record<string, any>;
  validation_result: DashboardValidationResult;
  correction_suggestions?: string[];
}

export interface HumanFeedbackResponse {
  corrected_json: Record<string, any>;
  feedback?: string;
}

export interface TaskResponse {
  task_id: string;
  status: 'pending' | 'completed' | 'failed';
  result?: {
    dashboard_json: Record<string, any>;
    validation_passed: boolean;
    required_human_intervention: boolean;
    retry_count: number;
  };
  error?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
} 