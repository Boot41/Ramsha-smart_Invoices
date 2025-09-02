import React, { useState, useEffect } from 'react';
import { 
  X, 
  CheckCircle, 
  Circle, 
  AlertCircle, 
  User, 
  FileText, 
  Eye, 
  Settings,
  Loader2,
  Pause,
  Download,
  ExternalLink,
  Brain,
  Sparkles,
  Target
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import HumanInputForm from './HumanInputForm';
import type { WorkflowEvent } from '../../services/websocketService';

interface WorkflowPopupProps {
  workflowId: string;
  contractName: string;
  isOpen: boolean;
  onClose: () => void;
  workflowStatus: any;
  events: WorkflowEvent[];
  onDownloadData?: () => void;
  onViewTemplates?: () => void;
  humanInputRequest?: any;
  onSubmitHumanInput?: (fieldValues: Record<string, any>, userNotes: string) => void;
  onCancelHumanInput?: () => void;
}

interface AgentStep {
  id: string;
  name: string;
  displayName: string;
  icon: React.ReactNode;
  description: string;
  detailedDescription: string;
  status: 'pending' | 'active' | 'completed' | 'failed' | 'needs_input' | 'paused';
  progress?: number;
  message?: string;
  timestamp?: string;
  duration?: number;
  substeps?: string[];
}

const WorkflowPopup: React.FC<WorkflowPopupProps> = ({
  workflowId,
  contractName,
  isOpen,
  onClose,
  workflowStatus,
  events,
  onDownloadData,
  onViewTemplates,
  humanInputRequest,
  onSubmitHumanInput,
  onCancelHumanInput
}) => {
  const [steps, setSteps] = useState<AgentStep[]>([
    {
      id: 'orchestrator',
      name: 'orchestrator',
      displayName: 'Workflow Orchestrator',
      icon: <Settings className="h-5 w-5" />,
      description: 'Analyzing workflow requirements and coordinating agents',
      detailedDescription: 'The orchestrator is analyzing the uploaded contract and determining the optimal processing strategy. It coordinates all other agents and manages the workflow state.',
      status: 'pending',
      message: 'Initializing workflow...',
      substeps: [
        'Parsing contract file',
        'Analyzing document structure',
        'Planning agent sequence',
        'Setting up workflow state'
      ]
    },
    {
      id: 'contract_processing',
      name: 'contract_processing',
      displayName: 'Contract Processing',
      icon: <FileText className="h-5 w-5" />,
      description: 'Extracting text and analyzing contract content',
      detailedDescription: 'This agent uses advanced PDF processing and OCR to extract text from your contract. It identifies key sections, clauses, and data fields.',
      status: 'pending',
      substeps: [
        'PDF text extraction',
        'OCR processing for scanned content',
        'Document structure analysis',
        'Key section identification'
      ]
    },
    {
      id: 'validation',
      name: 'validation',
      displayName: 'Data Validation',
      icon: <Eye className="h-5 w-5" />,
      description: 'Validating extracted data and checking for completeness',
      detailedDescription: 'The validation agent reviews all extracted data for accuracy and completeness. It checks for missing fields, validates formats, and identifies potential issues.',
      status: 'pending',
      substeps: [
        'Data completeness check',
        'Format validation',
        'Cross-reference verification',
        'Confidence scoring'
      ]
    },
    {
      id: 'correction',
      name: 'correction',
      displayName: 'Data Correction',
      icon: <Target className="h-5 w-5" />,
      description: 'Applying corrections and finalizing invoice data',
      detailedDescription: 'This agent applies any human corrections and performs final data cleaning. It ensures all invoice fields are properly formatted and complete.',
      status: 'pending',
      substeps: [
        'Applying human corrections',
        'Data normalization',
        'Field validation',
        'Final quality check'
      ]
    },
    {
      id: 'ui_invoice_generator',
      name: 'ui_invoice_generator',
      displayName: 'UI Template Generation',
      icon: <Sparkles className="h-5 w-5" />,
      description: 'Generating professional React invoice template',
      detailedDescription: 'The final agent creates a beautiful, professional React invoice component tailored to your contract data. It generates multiple template variations.',
      status: 'pending',
      substeps: [
        'Template design selection',
        'Component generation',
        'Style customization',
        'Export preparation'
      ]
    }
  ]);

  const [overallProgress, setOverallProgress] = useState(0);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [qualityScore, setQualityScore] = useState<number | null>(null);
  const [confidenceLevel, setConfidenceLevel] = useState<number | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [estimatedTimeRemaining] = useState<number | null>(null);
  const [startTime] = useState(Date.now());

  // Update steps based on workflow status and events
  useEffect(() => {
    updateStepsFromStatus();
  }, [workflowStatus, events]);

  // Auto-scroll to active step
  useEffect(() => {
    if (currentAgent) {
      const activeElement = document.getElementById(`step-${currentAgent}`);
      if (activeElement) {
        activeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [currentAgent]);

  const updateStepsFromStatus = () => {
    if (!workflowStatus && events.length === 0) return;

    const newSteps = [...steps];
    let newCurrentAgent = currentAgent;
    let newOverallProgress = 0;
    let newQualityScore = qualityScore;
    let newConfidenceLevel = confidenceLevel;
    let newIsCompleted = false;
    let newHasError = false;
    let newIsPaused = false;

    // Update from workflow status
    if (workflowStatus) {
      newCurrentAgent = workflowStatus.current_agent;
      newQualityScore = workflowStatus.quality_score;
      newConfidenceLevel = workflowStatus.confidence_level;

      const processingStatus = workflowStatus.processing_status || workflowStatus.status;
      
      if (processingStatus === 'completed' || processingStatus === 'success') {
        newIsCompleted = true;
        newOverallProgress = 100;
      } else if (processingStatus === 'failed' || processingStatus === 'error') {
        newHasError = true;
      } else if (processingStatus === 'needs_human_input') {
        newIsPaused = true;
        const validationIndex = newSteps.findIndex(s => s.id === 'validation');
        if (validationIndex >= 0) {
          newSteps[validationIndex].status = 'needs_input';
          newSteps[validationIndex].message = 'Human input required for validation';
        }
      }
    }

    // Process events
    events.forEach(event => {
      const eventType = event.type;
      const eventData = event.data;
      
      switch (eventType) {
        case 'agent_transition':
        case 'agent_started':
        case 'status_update':
          if (eventData.current_agent) {
            newCurrentAgent = eventData.current_agent;
            
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
                  
                  // Calculate duration if we have timestamps
                  if (newSteps[i].timestamp && event.timestamp) {
                    const duration = new Date(event.timestamp).getTime() - new Date(newSteps[i].timestamp!).getTime();
                    newSteps[i].duration = Math.round(duration / 1000);
                  }
                }
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
          newIsPaused = true;
          const validationStep = newSteps.find(s => s.id === 'validation');
          if (validationStep) {
            validationStep.status = 'needs_input';
            validationStep.message = eventData.instructions || 'Human input required';
          }
          break;

        case 'input_processed':
          newIsPaused = false;
          const validationStepProcessed = newSteps.find(s => s.id === 'validation');
          if (validationStepProcessed) {
            validationStepProcessed.status = 'completed';
            validationStepProcessed.message = 'Validation completed with human input';
          }
          break;

        case 'workflow_complete':
          newIsCompleted = true;
          newOverallProgress = 100;
          newSteps.forEach(step => {
            if (step.status === 'active' || step.status === 'pending') {
              step.status = 'completed';
              step.message = 'Completed successfully';
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
    setIsPaused(newIsPaused);
  };

  const getStepIcon = (step: AgentStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'active':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'needs_input':
        return <User className="h-5 w-5 text-yellow-500 animate-pulse" />;
      case 'paused':
        return <Pause className="h-5 w-5 text-orange-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-300" />;
    }
  };

  const getStepStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" className="text-xs animate-pulse">✓ Completed</Badge>;
      case 'active':
        return <Badge variant="primary" className="text-xs animate-pulse">🔄 Running</Badge>;
      case 'failed':
        return <Badge variant="error" className="text-xs">❌ Failed</Badge>;
      case 'needs_input':
        return <Badge variant="warning" className="text-xs animate-bounce">⏸️ Needs Input</Badge>;
      case 'paused':
        return <Badge variant="secondary" className="text-xs">⏸️ Paused</Badge>;
      default:
        return <Badge variant="secondary" className="text-xs">⏳ Waiting</Badge>;
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getTimeEstimate = () => {
    const elapsed = (Date.now() - startTime) / 1000;
    const completedSteps = steps.filter(s => s.status === 'completed').length;
    const totalSteps = steps.length;
    
    if (completedSteps > 0) {
      const avgTimePerStep = elapsed / completedSteps;
      const remainingSteps = totalSteps - completedSteps;
      return Math.round(avgTimePerStep * remainingSteps);
    }
    
    return null;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
                <Brain className="h-6 w-6 text-blue-600 mr-2" />
                Smart Contract Processing
              </CardTitle>
              <p className="text-sm text-gray-600 mt-1">
                Processing: <span className="font-medium">{contractName}</span>
              </p>
              <p className="text-xs text-gray-500">
                Workflow ID: {workflowId}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {/* Status indicators */}
              {isCompleted && (
                <div className="flex items-center text-green-600">
                  <CheckCircle className="h-5 w-5 mr-1" />
                  <span className="text-sm font-medium">Complete!</span>
                </div>
              )}
              {hasError && (
                <div className="flex items-center text-red-600">
                  <AlertCircle className="h-5 w-5 mr-1" />
                  <span className="text-sm font-medium">Error</span>
                </div>
              )}
              {isPaused && (
                <div className="flex items-center text-yellow-600">
                  <Pause className="h-5 w-5 mr-1" />
                  <span className="text-sm font-medium">Paused</span>
                </div>
              )}
              
              <Button variant="outline" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Overall Progress Bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>Overall Progress: {overallProgress}%</span>
              <div className="flex space-x-4">
                {qualityScore !== null && (
                  <span>Quality: {(qualityScore * 100).toFixed(0)}%</span>
                )}
                {confidenceLevel !== null && (
                  <span>Confidence: {(confidenceLevel * 100).toFixed(0)}%</span>
                )}
                {getTimeEstimate() && !isCompleted && (
                  <span>ETA: {formatDuration(getTimeEstimate()!)}</span>
                )}
              </div>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-3 relative overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-1000 relative ${
                  hasError ? 'bg-red-500' : isCompleted ? 'bg-green-500' : 'bg-gradient-to-r from-blue-500 to-purple-500'
                }`}
                style={{ width: `${overallProgress}%` }}
              >
                {/* Animated shimmer effect */}
                {!isCompleted && !hasError && (
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
                )}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="max-h-[50vh] overflow-y-auto">
            {/* Human Input Form */}
            {humanInputRequest && onSubmitHumanInput && onCancelHumanInput && (
              <div className="p-6 border-b bg-yellow-50">
                <HumanInputForm
                  request={humanInputRequest}
                  onSubmit={onSubmitHumanInput}
                  onCancel={onCancelHumanInput}
                />
              </div>
            )}

            {/* Agent Steps */}
            <div className="p-6 space-y-6">
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  id={`step-${step.name}`}
                  className={`relative ${
                    step.status === 'active' ? 'ring-2 ring-blue-500 ring-opacity-50 rounded-lg p-4 bg-blue-50' : 'p-4'
                  } transition-all duration-300`}
                >
                  {/* Connection line */}
                  {index < steps.length - 1 && (
                    <div className="absolute left-6 top-16 w-0.5 h-8 bg-gray-200" />
                  )}

                  <div className="flex items-start space-x-4">
                    {/* Step Icon */}
                    <div className={`flex-shrink-0 relative ${
                      step.status === 'active' ? 'animate-pulse' : ''
                    }`}>
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                        step.status === 'completed' ? 'bg-green-100' :
                        step.status === 'active' ? 'bg-blue-100' :
                        step.status === 'failed' ? 'bg-red-100' :
                        step.status === 'needs_input' ? 'bg-yellow-100' :
                        'bg-gray-100'
                      }`}>
                        {getStepIcon(step)}
                      </div>
                      
                      {/* Step number */}
                      <div className="absolute -top-1 -right-1 w-6 h-6 bg-white border-2 border-gray-200 rounded-full flex items-center justify-center text-xs font-bold">
                        {index + 1}
                      </div>
                    </div>

                    {/* Step Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-lg font-semibold text-gray-900 flex items-center">
                          {step.icon}
                          <span className="ml-2">{step.displayName}</span>
                        </h4>
                        {getStepStatusBadge(step.status)}
                      </div>

                      <p className="text-sm text-gray-600 mb-2">
                        {step.detailedDescription}
                      </p>

                      {/* Current status message */}
                      {step.message && (
                        <p className={`text-sm font-medium mb-2 ${
                          step.status === 'active' ? 'text-blue-600' :
                          step.status === 'completed' ? 'text-green-600' :
                          step.status === 'failed' ? 'text-red-600' :
                          step.status === 'needs_input' ? 'text-yellow-600' :
                          'text-gray-500'
                        }`}>
                          {step.message}
                        </p>
                      )}

                      {/* Substeps */}
                      {step.status === 'active' && step.substeps && (
                        <div className="mt-3 space-y-1">
                          {step.substeps.map((substep, subIndex) => (
                            <div key={subIndex} className="flex items-center text-xs text-gray-500">
                              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mr-2 animate-pulse" />
                              {substep}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Progress bar for active step */}
                      {step.status === 'active' && step.progress !== undefined && (
                        <div className="mt-3">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${step.progress}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Timestamp and duration */}
                      <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                        {step.timestamp && (
                          <span>
                            Started: {new Date(step.timestamp).toLocaleTimeString()}
                          </span>
                        )}
                        {step.duration && (
                          <span>
                            Duration: {formatDuration(step.duration)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer Actions */}
          <div className="border-t p-6 bg-gray-50">
            {isCompleted && (
              <div className="space-y-3">
                <div className="text-center">
                  <div className="inline-flex items-center text-green-600 mb-2">
                    <CheckCircle className="h-6 w-6 mr-2" />
                    <span className="text-lg font-semibold">Processing Complete!</span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Your contract has been successfully processed and invoice templates are ready.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {onDownloadData && (
                    <Button
                      onClick={onDownloadData}
                      variant="outline"
                      className="flex items-center justify-center"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download Invoice Data
                    </Button>
                  )}
                  
                  {onViewTemplates && (
                    <Button
                      onClick={onViewTemplates}
                      variant="primary"
                      className="flex items-center justify-center"
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      View Generated Templates
                    </Button>
                  )}
                </div>
              </div>
            )}

            {hasError && (
              <div className="text-center">
                <div className="inline-flex items-center text-red-600 mb-2">
                  <AlertCircle className="h-6 w-6 mr-2" />
                  <span className="text-lg font-semibold">Processing Failed</span>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  An error occurred during processing. Please try again or contact support.
                </p>
                <Button variant="outline" onClick={onClose}>
                  Close
                </Button>
              </div>
            )}

            {!isCompleted && !hasError && (
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  Processing your contract... Please keep this window open.
                </div>
                <Button variant="outline" onClick={onClose}>
                  Minimize
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WorkflowPopup;