'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { ModelProvider } from '../types/dashboard';
import { dashboardService } from '../domain/services/dashboardService';

interface DashboardFormInputs {
  prompt: string;
  model_provider: ModelProvider;
}

interface ModelOption {
  id: string;
  name: string;
}

interface DashboardGeneratorFormProps {
  onTaskCreated: (taskId: string) => void;
  models: ModelOption[];
}

export default function DashboardGeneratorForm({ onTaskCreated, models }: DashboardGeneratorFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DashboardFormInputs>({
    defaultValues: {
      model_provider: 'openai4o' as ModelProvider,
    },
  });
  
  const onSubmit = async (data: DashboardFormInputs) => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      const response = await dashboardService.generateDashboard({
        prompt: data.prompt,
        model_provider: data.model_provider,
      });
      
      onTaskCreated(response.task_id);
    } catch (err) {
      setError('Failed to create dashboard generation task. Please try again.');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Dashboard Generator</h2>
      
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="mb-4">
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-1">
            Dashboard Description
          </label>
          <textarea
            id="prompt"
            rows={5}
            className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="Describe the dashboard you want to generate, e.g., 'Create a Grafana dashboard for PostgreSQL database monitoring with panels for connections, query performance, and disk usage.'"
            {...register('prompt', { required: 'Please enter a dashboard description' })}
          />
          {errors.prompt && (
            <p className="mt-1 text-sm text-red-600">{errors.prompt.message}</p>
          )}
        </div>
        
        <div className="mb-6">
          <label htmlFor="model_provider" className="block text-sm font-medium text-gray-700 mb-1">
            AI Model
          </label>
          <select
            id="model_provider"
            className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
            {...register('model_provider')}
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-md mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Tips for effective dashboard prompts:</h3>
          <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
            <li>Include specific data sources (e.g., PostgreSQL, Prometheus, Elasticsearch)</li>
            <li>Mention specific metrics you want to track</li>
            <li>Specify panel types (line graphs, counters, gauges, etc.)</li>
            <li>Include sample SQL queries if you have them</li>
            <li>Describe the layout or organization you prefer</li>
          </ul>
        </div>
        
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isSubmitting ? 'Generating...' : 'Generate Dashboard'}
        </button>
      </form>
    </div>
  );
} 