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
  id: ModelProvider;
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
      model_provider: 'gpt-4o' as ModelProvider,
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
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">Dashboard Generator</h2>
      
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="mb-4">
          <label htmlFor="prompt" className="form-label">
            Dashboard Description
          </label>
          <textarea
            id="prompt"
            rows={5}
            className="form-input w-full max-w-full box-border"
            placeholder="Describe the dashboard you want to generate, e.g., 'Create a Grafana dashboard for PostgreSQL database monitoring with panels for connections, query performance, and disk usage.'"
            {...register('prompt', { required: 'Please enter a dashboard description' })}
          />
          {errors.prompt && (
            <p className="mt-1 text-sm text-red-600">{errors.prompt.message}</p>
          )}
        </div>
        
        <div className="mb-6">
          <label htmlFor="model_provider" className="form-label">
            AI Model
          </label>
          <select
            id="model_provider"
            className="form-input w-full"
            {...register('model_provider')}
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="tips-section">
          <h3 className="tips-title">Tips for effective dashboard prompts:</h3>
          <ul className="tips-list">
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
          className="btn btn-primary w-full"
        >
          {isSubmitting ? 'Generating...' : 'Generate Dashboard'}
        </button>
      </form>
    </div>
  );
} 