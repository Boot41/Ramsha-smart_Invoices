import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  Circle, 
  Clock, 
  AlertCircle, 
  User, 
  FileText, 
  Eye, 
  Settings,
  Zap,
  Download,
  ExternalLink,
  Loader2
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { WorkflowEvent } from '../../services/websocketService';
import { workflowAPI } from '../../services/workflowService';

interface WorkflowStatusTrackerProps {
  workflowId: string;
  workflowStatus: any;
  events: WorkflowEvent[];
}

interface AgentStep {
  id: string;
  name: string;
  displayName: string;
  icon: React.ReactNode;
  description: string;
  status: 'pending' | 'active' | 'completed' | 'failed' | 'needs_input';
  progress?: number;
  message?: string;
  timestamp?: string;
}

const WorkflowStatusTracker: React.FC<WorkflowStatusTrackerProps> = ({
  workflowId,
  workflowStatus,
  events
}) => {
  const [steps, setSteps] = useState<AgentStep[]>([
    {
      id: 'orchestrator',
      name: 'orchestrator',
      displayName: 'Workflow Orchestrator',
      icon: <Settings className="h-4 w-4" />,
      description: 'Analyzing workflow requirements and coordinating agents',
      status: 'pending',
      message: 'Waiting to start...'
    },
    {
      id: 'contract_processing',
      name: 'contract_processing',
      displayName: 'Contract Processing',
      icon: <FileText className="h-4 w-4" />,
      description: 'Extracting text and analyzing contract content',
      status: 'pending'
    },
    {
      id: 'validation',
      name: 'validation',
      displayName: 'Data Validation',
      icon: <Eye className="h-4 w-4" />,
      description: 'Validating extracted data and checking for completeness',
      status: 'pending'
    },
    {
      id: 'correction',
      name: 'correction',
      displayName: 'Data Correction',
      icon: <Settings className="h-4 w-4" />,
      description: 'Applying corrections and finalizing invoice data',
      status: 'pending'
    },
    {
      id: 'ui_invoice_generator',
      name: 'ui_invoice_generator',
      displayName: 'UI Template Generation',
      icon: <Zap className="h-4 w-4" />,
      description: 'Generating professional React invoice template',
      status: 'pending'
    }
  ]);

  const [overallProgress, setOverallProgress] = useState(0);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [qualityScore, setQualityScore] = useState<number | null>(null);
  const [confidenceLevel, setConfidenceLevel] = useState<number | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [finalResults, setFinalResults] = useState<any>(null);

  // Update steps based on workflow status and events
  useEffect(() => {
    updateStepsFromStatus();
  }, [workflowStatus, events]);

  const updateStepsFromStatus = () => {
    if (!workflowStatus && events.length === 0) return;

    const newSteps = [...steps];
    let newCurrentAgent = currentAgent;
    let newOverallProgress = 0;
    let newQualityScore = qualityScore;
    let newConfidenceLevel = confidenceLevel;
    let newIsCompleted = false;
    let newHasError = false;

    // Update from workflow status
    if (workflowStatus) {
      newCurrentAgent = workflowStatus.current_agent;
      newQualityScore = workflowStatus.quality_score;
      newConfidenceLevel = workflowStatus.confidence_level;

      // Map processing status to step status
      const processingStatus = workflowStatus.processing_status || workflowStatus.status;
      
      if (processingStatus === 'completed' || processingStatus === 'success') {
        newIsCompleted = true;
        newOverallProgress = 100;
      } else if (processingStatus === 'failed' || processingStatus === 'error') {
        newHasError = true;
      } else if (processingStatus === 'needs_human_input') {
        // Find validation step and mark as needs input
        const validationIndex = newSteps.findIndex(s => s.id === 'validation');
        if (validationIndex >= 0) {
          newSteps[validationIndex].status = 'needs_input';
          newSteps[validationIndex].message = 'Human input required for validation';
        }
      }
    }

    // Process events to update step statuses
    events.forEach(event => {
      const eventType = event.type;
      const eventData = event.data;
      
      switch (eventType) {
        case 'agent_transition':
        case 'agent_started':
        case 'status_update':
          if (eventData.current_agent) {
            newCurrentAgent = eventData.current_agent;
            
            // Update current agent step to active with specific message
            const activeStepIndex = newSteps.findIndex(s => s.name === eventData.current_agent);
            if (activeStepIndex >= 0) {
              newSteps[activeStepIndex].status = 'active';
              newSteps[activeStepIndex].timestamp = event.timestamp;
              newSteps[activeStepIndex].message = eventData.message || 
                `${newSteps[activeStepIndex].displayName} is processing...`;
              
              // Mark previous steps as completed
              for (let i = 0; i < activeStepIndex; i++) {
                if (newSteps[i].status !== 'completed') {
                  newSteps[i].status = 'completed';
                  newSteps[i].message = 'Completed successfully';
                }
              }
            }
          }
          
          // Update specific agent messages
          if (eventData.agent_name && eventData.message) {
            const agentStepIndex = newSteps.findIndex(s => s.name === eventData.agent_name);
            if (agentStepIndex >= 0) {
              newSteps[agentStepIndex].message = eventData.message;
              if (eventData.progress !== undefined) {
                newSteps[agentStepIndex].progress = eventData.progress;
              }
            }
          }
          
          if (eventData.progress_percentage !== undefined) {
            newOverallProgress = eventData.progress_percentage;
          }
          
          if (eventData.quality_score !== undefined) {
            newQualityScore = eventData.quality_score;
          }
          
          if (eventData.confidence_level !== undefined) {
            newConfidenceLevel = eventData.confidence_level;
          }
          break;

        case 'human_input_needed':
          const validationStep = newSteps.find(s => s.id === 'validation');
          if (validationStep) {
            validationStep.status = 'needs_input';
            validationStep.message = eventData.instructions || 'Human input required';
          }
          break;

        case 'input_processed':
          const validationStepProcessed = newSteps.find(s => s.id === 'validation');
          if (validationStepProcessed) {
            validationStepProcessed.status = 'completed';
            validationStepProcessed.message = 'Validation completed with human input';
          }
          break;

        case 'workflow_complete':
          newIsCompleted = true;
          newOverallProgress = 100;
          // Mark all steps as completed
          newSteps.forEach(step => {
            if (step.status === 'active' || step.status === 'pending') {
              step.status = 'completed';
            }
          });
          break;

        case 'workflow_error':
        case 'error':
          newHasError = true;
          if (newCurrentAgent) {
            const errorStepIndex = newSteps.findIndex(s => s.name === newCurrentAgent);
            if (errorStepIndex >= 0) {
              newSteps[errorStepIndex].status = 'failed';
              newSteps[errorStepIndex].message = eventData.message || 'Step failed';
            }
          }
          break;
      }
    });

    // Update states
    setSteps(newSteps);
    setCurrentAgent(newCurrentAgent);
    setOverallProgress(newOverallProgress);
    setQualityScore(newQualityScore);
    setConfidenceLevel(newConfidenceLevel);
    setIsCompleted(newIsCompleted);
    setHasError(newHasError);
  };

  const getStepIcon = (step: AgentStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'active':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'needs_input':
        return <User className="h-4 w-4 text-yellow-500" />;
      default:
        return <Circle className="h-4 w-4 text-gray-300" />;
    }
  };

  const getStepStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" className="text-xs">Completed</Badge>;
      case 'active':
        return <Badge variant="primary" className="text-xs">In Progress</Badge>;
      case 'failed':
        return <Badge variant="error" className="text-xs">Failed</Badge>;
      case 'needs_input':
        return <Badge variant="warning" className="text-xs">Needs Input</Badge>;
      default:
        return <Badge variant="secondary" className="text-xs">Pending</Badge>;
    }
  };

  const downloadInvoiceData = async () => {
    try {
      const data = await workflowAPI.getWorkflowInvoiceData(workflowId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-data-${workflowId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download invoice data:', error);
    }
  };

  const viewInvoiceTemplates = () => {
    // Navigate to templates page - adjust based on your routing
    window.open('/invoices/templates', '_blank');
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            🔄 Workflow Progress
          </h3>
          {isCompleted && (
            <Badge variant="success" className="animate-pulse">
              ✅ Completed
            </Badge>
          )}
          {hasError && (
            <Badge variant="error">
              ❌ Error
            </Badge>
          )}
        </div>
        
        {/* Overall Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              hasError ? 'bg-red-500' : isCompleted ? 'bg-green-500' : 'bg-blue-500'
            }`}
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Progress: {overallProgress}%</span>
          {qualityScore !== null && (
            <span>Quality: {(qualityScore * 100).toFixed(0)}%</span>
          )}
          {confidenceLevel !== null && (
            <span>Confidence: {(confidenceLevel * 100).toFixed(0)}%</span>
          )}
        </div>
      </div>

      {/* Agent Steps */}
      <div className="space-y-4">
        {steps.map((step) => (
          <div key={step.id} className="flex items-start space-x-3">
            {/* Step Icon */}
            <div className="flex-shrink-0 mt-1">
              {getStepIcon(step)}
            </div>
            
            {/* Step Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-900">
                  {step.displayName}
                </h4>
                {getStepStatusBadge(step.status)}
              </div>
              
              <p className="text-xs text-gray-600 mt-1">
                {step.message || step.description}
              </p>
              
              {step.timestamp && (
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(step.timestamp).toLocaleTimeString()}
                </p>
              )}
              
              {/* Progress bar for active step */}
              {step.status === 'active' && step.progress !== undefined && (
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-1">
                    <div
                      className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                      style={{ width: `${step.progress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      {isCompleted && (
        <div className="mt-6 space-y-2">
          <Button
            onClick={downloadInvoiceData}
            variant="outline"
            className="w-full"
            size="sm"
          >
            <Download className="mr-2 h-4 w-4" />
            Download Invoice Data
          </Button>
          
          <Button
            onClick={viewInvoiceTemplates}
            variant="outline"
            className="w-full"
            size="sm"
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            View Generated Templates
          </Button>
        </div>
      )}

      {/* Recent Events */}
      {events.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">
            📋 Recent Events
          </h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {events.slice(-5).reverse().map((event, index) => (
              <div key={index} className="text-xs p-2 bg-gray-50 rounded border">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-700">
                    {event.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  {event.timestamp && (
                    <span className="text-gray-400">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                {event.data.message && (
                  <p className="text-gray-600 mt-1">
                    {event.data.message}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

export default WorkflowStatusTracker;