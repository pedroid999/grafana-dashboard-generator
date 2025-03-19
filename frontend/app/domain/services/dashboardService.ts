/**
 * Dashboard domain service
 */

import { dashboardApi } from '../../adapters/api/dashboardApi';
import { 
  DashboardGenerationRequest, 
  HumanFeedbackResponse, 
  ModelInfo, 
  TaskResponse 
} from '../../types/dashboard';

/**
 * Service for dashboard operations
 */
export const dashboardService = {
  /**
   * Generate a dashboard based on natural language prompt
   */
  generateDashboard: async (request: DashboardGenerationRequest): Promise<TaskResponse> => {
    // Default values if not provided
    const completeRequest: DashboardGenerationRequest = {
      max_retries: 3,
      use_rag: true,
      ...request,
    };
    
    return dashboardApi.generateDashboard(completeRequest);
  },
  
  /**
   * Poll for dashboard generation task status
   */
  pollTaskStatus: async (taskId: string, onUpdate: (status: TaskResponse) => void, intervalMs = 2000): Promise<void> => {
    const checkStatus = async () => {
      const status = await dashboardApi.getTaskStatus(taskId);
      onUpdate(status);
      
      if (status.status === 'pending') {
        // Keep polling if still pending
        setTimeout(checkStatus, intervalMs);
      }
    };
    
    // Start polling
    checkStatus();
  },
  
  /**
   * Submit human feedback for a dashboard that needs intervention
   */
  submitHumanFeedback: async (taskId: string, feedback: HumanFeedbackResponse): Promise<TaskResponse> => {
    return dashboardApi.submitHumanFeedback(taskId, feedback);
  },
  
  /**
   * Get available models
   */
  getAvailableModels: async (): Promise<ModelInfo[]> => {
    return dashboardApi.getAvailableModels();
  },
  
  /**
   * Format JSON as a string for display
   */
  formatJsonForDisplay: (json: Record<string, unknown>): string => {
    return JSON.stringify(json, null, 2);
  },
}; 