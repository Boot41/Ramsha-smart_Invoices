import React, { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useInvoiceStore } from '../../../stores/invoiceStore';
import { workflowAPI } from '../../services/workflowService';

import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import HumanInputForm from '../../components/workflow/HumanInputForm';

const WorkflowTracker: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { setWorkflowId, setUiInvoiceComponent } = useInvoiceStore();
  
  // State management
  const [workflowStatus, setWorkflowStatus] = useState<any>(null);
  const [humanInputRequired, setHumanInputRequired] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [contractName, setContractName] = useState<string>('');

  // Get contract name from location state if available
  useEffect(() => {
    if (location.state?.contractName) {
      setContractName(location.state.contractName);
    }
  }, [location.state]);

  // ADK workflow polling logic
  useEffect(() => {
    if (!workflowId) return;
    
    setWorkflowId(workflowId);
    let pollInterval: NodeJS.Timeout;
    let isPolling = true;

    const pollWorkflowStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/adk/workflow/${workflowId}/status`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          }
        });

        if (response.ok) {
          const statusData = await response.json();
          console.log('🔄 Workflow status:', statusData);
          
          setWorkflowStatus(statusData);
          setIsLoading(false);
          setError(null);
          
          // Check if workflow needs human input
          if (statusData.status === 'needs_human_input' || 
              statusData.processing_status === 'needs_human_input' ||
              statusData.current_agent === 'validation') {
            
            console.log('🚨 Workflow needs human input - fetching requirements...');
            
            try {
              // Fetch human input requirements from ADK endpoint
              const humanInputResponse = await fetch(`http://localhost:8000/api/v1/adk/workflow/${workflowId}/human-input-request`, {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
              });
              
              if (humanInputResponse.ok) {
                const humanInputData = await humanInputResponse.json();
                console.log('📋 Human input requirements:', humanInputData);
                
                // Check if this is invoice validation - navigate to dedicated validation page
                if (statusData.current_agent === 'validation' || 
                    humanInputData.task_type === 'validation' ||
                    humanInputData.request_type === 'validation') {
                  console.log('🔄 Redirecting to invoice validation page...');
                  
                  // Navigate to the dedicated invoice validation page with all required data
                  navigate(`/invoices/validation/${workflowId}`, {
                    state: {
                      validationData: humanInputData,
                      workflowId: workflowId,
                      contractName: contractName || statusData.contract_name || 'Unknown Contract',
                      workflowStatus: statusData
                    }
                  });
                  return;
                }
                
                // For other types of human input, use the existing form
                setHumanInputRequired(humanInputData);
              }
            } catch (humanInputError) {
              console.error('❌ Error fetching human input requirements:', humanInputError);
            }
          }
          
          // Check if workflow is completed
          if (statusData.status === 'success' || 
              statusData.processing_status === 'success' ||
              statusData.progress_percentage === 100) {
            console.log('✅ Workflow completed successfully');
            isPolling = false;
            clearInterval(pollInterval);
          }
          
          // Check if workflow failed
          if (statusData.status === 'failed' || statusData.processing_status === 'failed') {
            console.log('❌ Workflow failed');
            isPolling = false;
            clearInterval(pollInterval);
          }
        } else {
          setError(`Failed to fetch workflow status: ${response.status}`);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('❌ Error polling workflow status:', error);
        setError('Failed to connect to workflow API');
        setIsLoading(false);
      }
    };

    // Start polling every 3 seconds
    pollInterval = setInterval(() => {
      if (isPolling) {
        pollWorkflowStatus();
      }
    }, 3000);
    
    // Initial poll
    pollWorkflowStatus();

    return () => {
      isPolling = false;
      clearInterval(pollInterval);
    };
  }, [workflowId, setWorkflowId]);

  const handleHumanInputSubmit = async (fieldValues: Record<string, any>, userNotes: string) => {
    try {
      console.log('📝 Submitting human input via ADK API...');
      
      // Submit human input via ADK endpoint
      const response = await fetch(`http://localhost:8000/api/v1/adk/workflow/human-input/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          workflow_id: workflowId,
          field_values: fieldValues,
          user_notes: userNotes
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Human input submitted successfully:', result);
        setHumanInputRequired(null);
        
        // Resume polling to get updated status
        // The polling logic will automatically detect the workflow continuation
      } else {
        const errorText = await response.text();
        throw new Error(`Failed to submit human input: ${response.status} ${errorText}`);
      }
    } catch (error) {
      console.error('❌ Failed to submit human input:', error);
      alert('Failed to submit input. Please try again.');
    }
  };

  const handleHumanInputCancel = () => {
    setHumanInputRequired(null);
    console.log('📝 Human input cancelled by user');
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'success':
      case 'completed':
        return 'success';
      case 'failed':
      case 'error':
        return 'error';
      case 'needs_human_input':
      case 'paused_for_validation':
        return 'warning';
      case 'in_progress':
      case 'pending':
        return 'info';
      default:
        return 'secondary';
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <h1 className="text-3xl font-bold text-slate-900">Loading Workflow...</h1>
          <p className="text-slate-600 mt-2">Fetching workflow status for {workflowId}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-3xl font-bold text-slate-900">Workflow Error</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <Button 
            onClick={() => window.location.reload()} 
            className="mt-2"
            variant="outline"
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">ADK Workflow Status</h1>
          <p className="text-slate-600 mt-2">
            {contractName && <span className="font-medium">{contractName}</span>}
            {contractName && ' • '}
            Workflow ID: {workflowId}
          </p>
        </div>
        <Button 
          onClick={() => navigate('/contracts')} 
          variant="outline"
        >
          Back to Contracts
        </Button>
      </div>

      {/* Workflow Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Current Status
            <Badge variant={getStatusBadgeVariant(workflowStatus?.status)}>
              {workflowStatus?.status || 'Unknown'}
            </Badge>
          </CardTitle>
          <CardDescription>
            Current Agent: {workflowStatus?.current_agent || 'None'} • 
            Progress: {Math.round(workflowStatus?.progress_percentage || 0)}%
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
              style={{ width: `${workflowStatus?.progress_percentage || 0}%` }}
            ></div>
          </div>
          {workflowStatus?.errors && workflowStatus.errors.length > 0 && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 className="font-medium text-red-800 mb-2">Errors:</h4>
              <ul className="space-y-1">
                {workflowStatus.errors.map((error: string, index: number) => (
                  <li key={index} className="text-red-700 text-sm">• {error}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Human Input Form */}
      {humanInputRequired && (
        <Card>
          <CardHeader>
            <CardTitle>Human Input Required</CardTitle>
            <CardDescription>The workflow needs your review and corrections to continue</CardDescription>
          </CardHeader>
          <CardContent>
            <HumanInputForm
              request={{
                fields: humanInputRequired.fields || [],
                instructions: humanInputRequired.instructions || humanInputRequired.message || 'Please review and correct the extracted data.',
                context: humanInputRequired.context || {},
                validation_errors: humanInputRequired.validation_errors || [],
                confidence_scores: humanInputRequired.confidence_scores || {}
              }}
              onSubmit={handleHumanInputSubmit}
              onCancel={handleHumanInputCancel}
            />
          </CardContent>
        </Card>
      )}

      {/* Workflow Details */}
      {workflowStatus && (
        <Card>
          <CardHeader>
            <CardTitle>Workflow Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="text-sm overflow-auto">
                {JSON.stringify(workflowStatus, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WorkflowTracker;
