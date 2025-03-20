'use client';

import { useEffect, useState } from 'react';
import { ModelInfo } from '../types/dashboard';
import { dashboardService } from '../domain/services/dashboardService';

/**
 * Custom hook to fetch available dashboard generation models
 */
export function useDashboardModels() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchModels = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const modelData = await dashboardService.getAvailableModels();
        setModels(modelData);
      } catch (err) {
        console.error('Failed to fetch models:', err);
        setError('Failed to load available models');
        // Fallback to default models if API fails
        setModels([
          { id: 'gpt-4o', name: 'GPT-4 Optimized (Default)' },
          { id: 'openai', name: 'OpenAI GPT-4 Turbo' },
          { id: 'o3-mini', name: 'OpenAI o3-mini' },
          { id: 'anthropic', name: 'Anthropic Claude 3 Opus' },
        ]);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchModels();
  }, []);
  
  return { models, isLoading, error };
} 