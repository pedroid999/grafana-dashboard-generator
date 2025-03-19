'use client';

import { useEffect, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react';
import { dashboardService } from '../domain/services/dashboardService';
import { TaskResponse, HumanFeedbackResponse } from '../types/dashboard';

interface DashboardResultProps {
  taskId: string;
  onReset: () => void;
}

export default function DashboardResult({ taskId, onReset }: DashboardResultProps) {
  const [taskStatus, setTaskStatus] = useState<TaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedbackJson, setFeedbackJson] = useState<string>('');
  const [feedbackMessage, setFeedbackMessage] = useState<string>('');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  
  // Poll for task status
  useEffect(() => {
    if (!taskId) return;
    
    dashboardService.pollTaskStatus(taskId, (status) => {
      setTaskStatus(status);
    });
  }, [taskId]);
  
  // When task requires human intervention, initialize feedback JSON
  useEffect(() => {
    if (
      taskStatus?.result?.required_human_intervention &&
      taskStatus.result.dashboard_json
    ) {
      setFeedbackJson(JSON.stringify(taskStatus.result.dashboard_json, null, 2));
    }
  }, [taskStatus]);
  
  const handleFeedbackSubmit = async () => {
    if (!taskId || !feedbackJson) return;
    
    setIsSubmittingFeedback(true);
    setError(null);
    
    try {
      // Parse the JSON string to validate it
      const jsonData = JSON.parse(feedbackJson);
      
      const feedback: HumanFeedbackResponse = {
        corrected_json: jsonData,
        feedback: feedbackMessage,
      };
      
      const response = await dashboardService.submitHumanFeedback(taskId, feedback);
      setTaskStatus(response);
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format. Please correct the JSON before submitting.');
      } else {
        setError('Failed to submit feedback. Please try again.');
        console.error(err);
      }
    } finally {
      setIsSubmittingFeedback(false);
    }
  };
  
  if (!taskStatus) {
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
    <div className="bg-white shadow-md rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Dashboard Generation Result</h2>
        <button
          onClick={onReset}
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          Start New Generation
        </button>
      </div>
      
      <div className="mb-6">
        <div className="flex items-center mb-2">
          <span className="font-medium text-gray-700 mr-2">Status:</span>
          <StatusBadge status={taskStatus.status} />
        </div>
        <div className="text-sm text-gray-600">
          <p>Task ID: {taskId}</p>
          {taskStatus.result?.retry_count !== undefined && (
            <p>Retry Count: {taskStatus.result.retry_count}</p>
          )}
        </div>
      </div>
      
      {/* Display error if any */}
      {(taskStatus.error || error) && (
        <div className="bg-red-50 text-red-600 p-4 rounded-md mb-6">
          <p className="font-medium">Error:</p>
          <p>{taskStatus.error || error}</p>
        </div>
      )}
      
      {/* Human feedback form when intervention required */}
      {taskStatus.status === 'completed' && 
       taskStatus.result?.required_human_intervention && (
        <div className="mb-6">
          <div className="bg-yellow-50 text-yellow-700 p-4 rounded-md mb-4">
            <div className="flex items-center mb-2">
              <AlertCircle size={20} className="mr-2" />
              <h3 className="font-medium">Human Intervention Required</h3>
            </div>
            <p className="text-sm">
              The dashboard JSON has validation errors that could not be automatically fixed.
              Please review and correct the JSON below.
            </p>
          </div>
          
          <div className="mb-4">
            <label htmlFor="feedbackJson" className="block text-sm font-medium text-gray-700 mb-1">
              Dashboard JSON (Edit to fix errors)
            </label>
            <textarea
              id="feedbackJson"
              rows={10}
              className="w-full font-mono text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              value={feedbackJson}
              onChange={(e) => setFeedbackJson(e.target.value)}
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="feedbackMessage" className="block text-sm font-medium text-gray-700 mb-1">
              Feedback Message (Optional)
            </label>
            <textarea
              id="feedbackMessage"
              rows={2}
              className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Any additional notes about your changes..."
              value={feedbackMessage}
              onChange={(e) => setFeedbackMessage(e.target.value)}
            />
          </div>
          
          <button
            onClick={handleFeedbackSubmit}
            disabled={isSubmittingFeedback}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isSubmittingFeedback ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </div>
      )}
      
      {/* Display JSON if valid result */}
      {taskStatus.status === 'completed' && 
       taskStatus.result?.dashboard_json && 
       !taskStatus.result?.required_human_intervention && (
        <div>
          <h3 className="font-medium text-gray-700 mb-2">Dashboard JSON</h3>
          <div className="border border-gray-200 rounded-md overflow-hidden">
            <SyntaxHighlighter 
              language="json" 
              style={vscDarkPlus}
              customStyle={{ margin: 0, maxHeight: '500px' }}
            >
              {JSON.stringify(taskStatus.result.dashboard_json, null, 2)}
            </SyntaxHighlighter>
          </div>
          <p className="mt-4 text-sm text-gray-600">
            You can now import this JSON into Grafana to create your dashboard.
          </p>
        </div>
      )}
    </div>
  );
}

// Status badge component
function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'pending':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <Clock size={14} className="mr-1" />
          Processing
        </span>
      );
    case 'completed':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircle size={14} className="mr-1" />
          Completed
        </span>
      );
    case 'failed':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <XCircle size={14} className="mr-1" />
          Failed
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          {status}
        </span>
      );
  }
} 