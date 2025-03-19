/**
 * API adapter for dashboard operations
 */

import axios from 'axios';
import { 
  DashboardGenerationRequest, 
  HumanFeedbackResponse, 
  ModelInfo, 
  TaskResponse 
} from '../../types/dashboard';

// API base URL - would be in env variable in production
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Dashboard API operations
 */
export const dashboardApi = {
  /**
   * Generate a dashboard from a natural language prompt
   */
  generateDashboard: async (request: DashboardGenerationRequest): Promise<TaskResponse> => {
    const response = await apiClient.post<TaskResponse>('/dashboards/generate', request);
    return response.data;
  },

  /**
   * Get the status of a dashboard generation task
   */
  getTaskStatus: async (taskId: string): Promise<TaskResponse> => {
    const response = await apiClient.get<TaskResponse>(`/tasks/${taskId}`);
    return response.data;
  },

  /**
   * Submit human feedback for a dashboard
   */
  submitHumanFeedback: async (taskId: string, feedback: HumanFeedbackResponse): Promise<TaskResponse> => {
    const response = await apiClient.post<TaskResponse>(`/tasks/${taskId}/feedback`, feedback);
    return response.data;
  },

  /**
   * List available LLM models
   */
  getAvailableModels: async (): Promise<ModelInfo[]> => {
    const response = await apiClient.get<{ models: ModelInfo[] }>('/models');
    return response.data.models;
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await apiClient.get<{ status: string }>('/health');
    return response.data;
  },
}; 