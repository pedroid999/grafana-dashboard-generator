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
    try {
      const response = await apiClient.get<TaskResponse>(`/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      console.warn('Error fetching task status, trying alternative route', error);
      try {
        // Intenta con ruta alternativa
        const altResponse = await apiClient.get<TaskResponse>(`/dashboard/tasks/${taskId}`);
        return altResponse.data;
      } catch (secondError) {
        console.error('Failed to fetch task status from both endpoints', secondError);
        throw secondError;
      }
    }
  },

  /**
   * Submit human feedback for a dashboard
   */
  submitHumanFeedback: async (taskId: string, feedback: HumanFeedbackResponse): Promise<TaskResponse> => {
    try {
      const response = await apiClient.post<TaskResponse>(`/tasks/${taskId}/feedback`, feedback);
      return response.data;
    } catch (error) {
      console.warn('Error submitting feedback, trying alternative route', error);
      try {
        // Intenta con ruta alternativa
        const altResponse = await apiClient.post<TaskResponse>(`/dashboard/tasks/${taskId}/feedback`, feedback);
        return altResponse.data;
      } catch (secondError) {
        console.error('Failed to submit feedback to both endpoints', secondError);
        throw secondError;
      }
    }
  },

  /**
   * List available LLM models
   */
  getAvailableModels: async (): Promise<ModelInfo[]> => {
    try {
      // Intenta primero con la ruta correcta
      const response = await apiClient.get<{ models: ModelInfo[] }>('/models');
      return response.data.models;
    } catch (error) {
      console.warn('Error fetching models from primary endpoint, trying alternative route', error);
      try {
        // Intenta con la ruta alternativa
        const altResponse = await apiClient.get<{ models: ModelInfo[] }>('/dashboard/models');
        return altResponse.data.models;
      } catch (secondError) {
        console.error('Failed to fetch models from both endpoints', secondError);
        // Devolver un array vacío y dejar que el hook maneje el fallback
        return [];
      }
    }
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await apiClient.get<{ status: string }>('/health');
    return response.data;
  },
}; 