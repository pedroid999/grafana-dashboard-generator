'use client';

import { useEffect, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { AlertCircle, CheckCircle, Clock, XCircle, Plus, Clipboard } from 'lucide-react';
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
    
    console.log("Starting to poll for task ID:", taskId);
    
    dashboardService.pollTaskStatus(taskId, (status) => {
      console.log("Task status update:", status);
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
      console.error("Error submitting feedback:", err);
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format. Please correct the JSON before submitting.');
      } else {
        setError('Failed to submit feedback. Please try again.');
      }
    } finally {
      setIsSubmittingFeedback(false);
    }
  };
  
  // Add a helper function to copy text to clipboard
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        // Could add a toast notification here if desired
        console.log('Text copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  };
  
  if (!taskStatus) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: 'var(--primary)' }}></div>
          <p className="mt-4" style={{ color: 'var(--gray-600)' }}>Loading task status for ID: {taskId}...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="card">
      <div className="flex flex-col mb-12">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Dashboard Generation Result</h2>
        </div>
        
        <div>
          <button
            onClick={onReset}
            className="btn font-medium px-4 py-2 bg-gray-100 hover:bg-gray-200 transition-colors inline-flex items-center justify-center"
            style={{ color: 'var(--primary)' }}
          >
            <Plus size={16} className="mr-2" style={{ marginTop: '-1px' }} />
            <span>Start New Generation</span>
          </button>
        </div>
      </div>
      
      <div className="p-5 bg-gray-50 rounded-md mb-6 border border-gray-200">
        <div className="flex items-center mb-3">
          <span className="font-medium mr-3" style={{ color: 'var(--gray-700)' }}>Status:</span>
          <StatusBadge status={taskStatus.status} />
        </div>
        <div style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>
          <p>Task ID: {taskId}</p>
          {taskStatus.result?.retry_count !== undefined && (
            <p className="mt-2">Retry Count: {taskStatus.result.retry_count}</p>
          )}
        </div>
      </div>
      
      {/* Display error if any */}
      {(taskStatus.error || error) && (
        <div style={{ 
          backgroundColor: '#FEF2F2', 
          color: '#DC2626', 
          padding: '1rem', 
          borderRadius: '0.375rem', 
          marginBottom: '1.5rem' 
        }}>
          <p className="font-medium">Error:</p>
          <p>{taskStatus.error || error}</p>
        </div>
      )}
      
      {/* Debug information */}
      <div style={{ 
        backgroundColor: '#EFF6FF', 
        padding: '1rem', 
        borderRadius: '0.375rem', 
        marginBottom: '1.5rem',
        fontFamily: 'monospace',
        fontSize: '0.875rem',
        position: 'relative'
      }}>
        <p className="font-medium mb-2">Debug Information:</p>
        <div className="relative">
          <div className="absolute top-0 right-0 flex items-center p-1 z-10">
            <button
              type="button"
              className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-200 hover:bg-gray-600 focus:outline-none flex items-center"
              onClick={() => copyToClipboard(JSON.stringify(taskStatus, null, 2))}
              title="Copy to clipboard"
            >
              <Clipboard size={12} className="mr-1" />
              Copy
            </button>
          </div>
          <SyntaxHighlighter 
            language="json" 
            style={vscDarkPlus}
            customStyle={{ margin: 0 }}
          >
            {JSON.stringify(taskStatus, null, 2)}
          </SyntaxHighlighter>
        </div>
        <p className="mt-2 text-xs">API Base URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}</p>
      </div>
      
      {/* Human feedback form when intervention required */}
      {taskStatus.status === 'completed' && 
       taskStatus.result?.required_human_intervention && (
        <div className="mb-6">
          <div style={{ 
            backgroundColor: '#FFFBEB', 
            color: '#B45309', 
            padding: '1rem', 
            borderRadius: '0.375rem', 
            marginBottom: '1rem' 
          }}>
            <div className="flex items-center mb-2">
              <AlertCircle size={20} className="mr-2" />
              <h3 className="font-medium">Human Intervention Required</h3>
            </div>
            <p style={{ fontSize: '0.875rem' }}>
              The dashboard JSON has validation errors that could not be automatically fixed.
              Please review and correct the JSON below.
            </p>
          </div>
          
          <div className="mb-4">
            <label htmlFor="feedbackJson" className="form-label">
              Dashboard JSON (Edit to fix errors)
            </label>
            <div className="relative">
              <div className="absolute top-0 right-0 flex items-center p-1 z-10">
                <button
                  type="button"
                  className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-200 hover:bg-gray-600 focus:outline-none flex items-center"
                  onClick={() => copyToClipboard(feedbackJson)}
                  title="Copy to clipboard"
                >
                  <Clipboard size={12} className="mr-1" />
                  Copy
                </button>
              </div>
              <textarea
                id="feedbackJson"
                rows={10}
                className="form-input font-mono text-sm w-full"
                value={feedbackJson}
                onChange={(e) => setFeedbackJson(e.target.value)}
              />
            </div>
          </div>
          
          <div className="mb-4">
            <label htmlFor="feedbackMessage" className="form-label">
              Feedback Message (Optional)
            </label>
            <textarea
              id="feedbackMessage"
              rows={2}
              className="form-input"
              placeholder="Any additional notes about your changes..."
              value={feedbackMessage}
              onChange={(e) => setFeedbackMessage(e.target.value)}
            />
          </div>
          
          <button
            onClick={handleFeedbackSubmit}
            disabled={isSubmittingFeedback}
            className="btn btn-primary w-full"
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
          <h3 className="font-medium mb-2" style={{ color: 'var(--gray-700)' }}>Dashboard JSON</h3>
          <div style={{ 
            border: '1px solid var(--gray-200)', 
            borderRadius: '0.375rem', 
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div className="absolute top-0 right-0 flex items-center p-1 z-10">
              <button
                type="button"
                className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-200 hover:bg-gray-600 focus:outline-none flex items-center"
                onClick={() => copyToClipboard(JSON.stringify(taskStatus.result?.dashboard_json, null, 2))}
                title="Copy to clipboard"
              >
                <Clipboard size={12} className="mr-1" />
                Copy
              </button>
            </div>
            <SyntaxHighlighter 
              language="json" 
              style={vscDarkPlus}
              customStyle={{ margin: 0, maxHeight: '500px' }}
            >
              {JSON.stringify(taskStatus.result?.dashboard_json, null, 2)}
            </SyntaxHighlighter>
          </div>
          <p className="mt-4" style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>
            You can now import this JSON into Grafana to create your dashboard.
          </p>
        </div>
      )}
    </div>
  );
}

// Status badge component
function StatusBadge({ status }: { status: string }) {
  const getBadgeStyles = (bgColor: string, textColor: string) => ({
    display: 'inline-flex',
    alignItems: 'center',
    padding: '0.125rem 0.625rem',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: '500',
    backgroundColor: bgColor,
    color: textColor
  });

  switch (status) {
    case 'pending':
      return (
        <span style={getBadgeStyles('#DBEAFE', '#1E40AF')}>
          <Clock size={14} style={{ marginRight: '0.25rem' }} />
          Processing
        </span>
      );
    case 'completed':
      return (
        <span style={getBadgeStyles('#DCFCE7', '#166534')}>
          <CheckCircle size={14} style={{ marginRight: '0.25rem' }} />
          Completed
        </span>
      );
    case 'failed':
      return (
        <span style={getBadgeStyles('#FEE2E2', '#B91C1C')}>
          <XCircle size={14} style={{ marginRight: '0.25rem' }} />
          Failed
        </span>
      );
    default:
      return (
        <span style={getBadgeStyles('#F3F4F6', '#374151')}>
          {status}
        </span>
      );
  }
} 