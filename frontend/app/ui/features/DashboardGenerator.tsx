'use client';

import { useState } from 'react';
import DashboardGeneratorForm from '../../components/DashboardGeneratorForm';
import DashboardResult from '../../components/DashboardResult';
import { useDashboardModels } from '../../hooks/useDashboardModels';

export default function DashboardGenerator() {
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const { models, isLoading, error } = useDashboardModels();
  
  const handleTaskCreated = (taskId: string) => {
    setActiveTaskId(taskId);
  };
  
  const handleReset = () => {
    setActiveTaskId(null);
  };
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-md mb-6">
          <p className="font-medium">Error:</p>
          <p>{error}</p>
        </div>
      )}
      
      {!activeTaskId ? (
        <DashboardGeneratorForm 
          onTaskCreated={handleTaskCreated} 
          models={models} 
        />
      ) : (
        <DashboardResult 
          taskId={activeTaskId} 
          onReset={handleReset} 
        />
      )}
    </div>
  );
} 