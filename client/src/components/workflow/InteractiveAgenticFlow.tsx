import React, { useState, useEffect, useCallback } from 'react';
import { 
  FileText, 
  Search, 
  User, 
  Settings, 
  Receipt, 
  CheckCircle,
  AlertCircle,
  Loader2,
  Edit3,
  Save,
  X,
  ArrowRight,
  Clock,
  MessageSquare,
  ChevronRight,
  Eye,
  Brain,
  Zap,
  Target,
  Sparkles
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { workflowWebSocket } from '../../services/websocketService';
import type { WorkflowEvent } from '../../services/websocketService';

interface ValidationField {
  id: string;
  label: string;
  value: string;
  type: 'text' | 'email' | 'number' | 'currency' | 'date' | 'textarea';
  required: boolean;
  validated: boolean;
  confidence: number;
  error?: string;
}

interface AgentStep {
  id: string;
  name: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'needs_input' | 'failed';
  progress: number;
  timestamp?: string;
  duration?: string;
}

interface InteractiveAgenticFlowProps {
  workflowId?: string;
  contractName?: string;
  onStepComplete?: (stepId: string, data?: any) => void;
  onWorkflowComplete?: (finalData: any) => void;
  workflowEvents?: WorkflowEvent[];
  realTimeMode?: boolean;
  humanInputData?: any;
  showHumanInputPopup?: boolean;
  onHumanInputSubmitted?: () => void;
  className?: string;
}

const InteractiveAgenticFlow: React.FC<InteractiveAgenticFlowProps> = ({
  workflowId,
  contractName,
  onStepComplete,
  onWorkflowComplete,
  workflowEvents = [],
  realTimeMode = false,
  humanInputData,
  showHumanInputPopup = false,
  onHumanInputSubmitted,
  className = ''
}) => {
  // Agent steps state
  const [steps, setSteps] = useState<AgentStep[]>([
    {
      id: 'processing',
      name: 'Contract Processing',
      icon: <Brain className="h-5 w-5" />,
      title: '🔍 Contract Processing Agent',
      description: 'AI agent analyzing document structure and extracting raw text data',
      status: 'pending',
      progress: 0
    },
    {
      id: 'validation',
      name: 'Data Validation',
      icon: <Target className="h-5 w-5" />,
      title: '🎯 Validation Agent',
      description: 'AI agent validating extracted data and identifying missing information',
      status: 'pending',
      progress: 0
    },
    {
      id: 'human_input',
      name: 'Human Input',
      icon: <User className="h-5 w-5" />,
      title: '👤 Human-in-the-Loop',
      description: 'Review extracted data and provide corrections for maximum accuracy',
      status: 'pending',
      progress: 0
    },
    {
      id: 'correction',
      name: 'Data Correction',
      icon: <Sparkles className="h-5 w-5" />,
      title: '✨ Correction Agent',
      description: 'AI agent applying human feedback and finalizing validated data',
      status: 'pending',
      progress: 0
    },
    {
      id: 'invoice_generation',
      name: 'Invoice Generation',
      icon: <Zap className="h-5 w-5" />,
      title: '⚡ Invoice Generator Agent',
      description: 'AI agent creating professional invoice template with verified data',
      status: 'pending',
      progress: 0
    }
  ]);

  // Current step tracking
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [overallProgress, setOverallProgress] = useState(0);

  // Validation data - will be populated from backend humanInputData
  const [validationFields, setValidationFields] = useState<ValidationField[]>([]);

  // Human input state
  const [isEditingField, setIsEditingField] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState('');
  const [humanInputCompleted, setHumanInputCompleted] = useState(false);

  // Final invoice data
  const [finalInvoiceData, setFinalInvoiceData] = useState<any>(null);

  // Update validation fields when humanInputData is received
  useEffect(() => {
    if (humanInputData && humanInputData.fields) {
      console.log('📋 Populating validation fields from backend data:', humanInputData.fields);
      const backendFields = humanInputData.fields.map((field: any) => ({
        id: field.name,
        label: field.label,
        value: field.value || '',
        type: field.type,
        required: field.required,
        validated: false,
        confidence: field.confidence || 0.5,
        error: field.validation_message
      }));
      setValidationFields(backendFields);
    }
  }, [humanInputData]);

  // Real-time websocket integration
  useEffect(() => {
    if (realTimeMode && workflowEvents.length > 0) {
      console.log('📡 Processing workflow events:', workflowEvents.length);
      updateStepsFromEvents(workflowEvents);
    } else if (!realTimeMode && currentStepIndex < steps.length) {
      const timer = setTimeout(() => {
        simulateStepProgress();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [currentStepIndex, workflowEvents, realTimeMode]);

  // Effect to handle showHumanInputPopup changes
  useEffect(() => {
    if (showHumanInputPopup) {
      console.log('🙋 Human input popup should show, validationFields:', validationFields.length);
      const humanStepIndex = steps.findIndex(s => s.id === 'human_input');
      if (humanStepIndex >= 0) {
        updateStepStatus(humanStepIndex, 'needs_input');
        setCurrentStepIndex(humanStepIndex);
      }
    }
  }, [showHumanInputPopup, validationFields]);

  // Update steps based on real websocket events
  const updateStepsFromEvents = (events: WorkflowEvent[]) => {
    const latestEvent = events[events.length - 1];
    if (!latestEvent) return;

    switch (latestEvent.type) {
      case 'status_update':
      case 'agent_transition':
        if (latestEvent.data.current_agent) {
          const agentName = latestEvent.data.current_agent;
          const stepIndex = steps.findIndex(s => 
            s.name.toLowerCase().includes(agentName.toLowerCase()) ||
            s.id.includes(agentName)
          );
          
          if (stepIndex >= 0) {
            updateStepStatus(stepIndex, 'processing');
            setCurrentStepIndex(stepIndex);
            
            // Mark previous steps as completed
            for (let i = 0; i < stepIndex; i++) {
              updateStepStatus(i, 'completed');
            }
          }
        }
        break;
        
      case 'human_input_needed':
        const humanStepIndex = steps.findIndex(s => s.id === 'human_input');
        if (humanStepIndex >= 0) {
          updateStepStatus(humanStepIndex, 'needs_input');
          setCurrentStepIndex(humanStepIndex);
          console.log('🙋 Setting human input step as needs_input');
        }
        break;
        
      case 'input_processed':
        const processedStepIndex = steps.findIndex(s => s.id === 'human_input');
        if (processedStepIndex >= 0) {
          updateStepStatus(processedStepIndex, 'completed');
          setCurrentStepIndex(processedStepIndex + 1);
        }
        break;
        
      case 'workflow_complete':
        // Mark all remaining steps as completed
        steps.forEach((_, index) => {
          updateStepStatus(index, 'completed');
        });
        setOverallProgress(100);
        break;
    }
  };

  const simulateStepProgress = () => {
    const currentStep = steps[currentStepIndex];
    
    if (currentStep.status === 'pending') {
      updateStepStatus(currentStepIndex, 'processing');
    } else if (currentStep.status === 'processing') {
      updateStepProgress(currentStepIndex, Math.min(currentStep.progress + 20, 100));
      
      if (currentStep.progress >= 100) {
        if (currentStep.id === 'validation') {
          // Validation step needs human input
          updateStepStatus(currentStepIndex, 'needs_input');
        } else if (currentStep.id === 'human_input') {
          // Wait for human input completion
          if (humanInputCompleted) {
            updateStepStatus(currentStepIndex, 'completed');
            setCurrentStepIndex(prev => prev + 1);
          }
        } else {
          updateStepStatus(currentStepIndex, 'completed');
          setCurrentStepIndex(prev => prev + 1);
        }
      }
    }
  };

  const updateStepStatus = (stepIndex: number, status: AgentStep['status']) => {
    setSteps(prev => prev.map((step, index) => 
      index === stepIndex 
        ? { ...step, status, timestamp: new Date().toLocaleTimeString() }
        : step
    ));
  };

  const updateStepProgress = (stepIndex: number, progress: number) => {
    setSteps(prev => prev.map((step, index) => 
      index === stepIndex ? { ...step, progress } : step
    ));
    
    // Update overall progress
    const completedSteps = steps.filter(step => step.status === 'completed').length;
    const currentStepProgress = progress / 100;
    const newOverallProgress = ((completedSteps + currentStepProgress) / steps.length) * 100;
    setOverallProgress(newOverallProgress);
  };

  const getStepStatusIcon = (step: AgentStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'needs_input':
        return <User className="h-5 w-5 text-yellow-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-gray-300" />;
    }
  };

  const getStepStatusColor = (step: AgentStep) => {
    switch (step.status) {
      case 'completed':
        return 'bg-green-100 border-green-200 text-green-800';
      case 'processing':
        return 'bg-blue-100 border-blue-200 text-blue-800';
      case 'needs_input':
        return 'bg-yellow-100 border-yellow-200 text-yellow-800';
      case 'failed':
        return 'bg-red-100 border-red-200 text-red-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-600';
    }
  };

  const handleFieldEdit = (fieldId: string) => {
    const field = validationFields.find(f => f.id === fieldId);
    if (field) {
      setIsEditingField(fieldId);
      setEditingValue(field.value);
    }
  };

  const handleFieldSave = (fieldId: string) => {
    setValidationFields(prev => prev.map(field => 
      field.id === fieldId 
        ? { ...field, value: editingValue, validated: true, confidence: 1.0 }
        : field
    ));
    setIsEditingField(null);
    setEditingValue('');
  };

  const handleFieldCancel = () => {
    setIsEditingField(null);
    setEditingValue('');
  };

  const handleCompleteHumanInput = async () => {
    if (!workflowId) {
      console.error('❌ No workflow ID available');
      return;
    }

    setHumanInputCompleted(true);
    
    try {
      // Convert validation fields to the format expected by backend
      const fieldValues = validationFields.reduce((acc, field) => {
        acc[field.id] = field.value;
        return acc;
      }, {} as Record<string, any>);

      console.log('🚀 Submitting human input:', fieldValues);
      
      // Submit through websocket service
      const success = await workflowWebSocket.submitValidationInput(fieldValues, 'User corrections applied');
      
      if (success) {
        updateStepStatus(currentStepIndex, 'completed');
        setCurrentStepIndex(prev => prev + 1);
        onStepComplete?.('human_input', validationFields);
        onHumanInputSubmitted?.();
      } else {
        console.error('❌ Failed to submit human input');
        setHumanInputCompleted(false);
      }
    } catch (error) {
      console.error('❌ Error submitting human input:', error);
      setHumanInputCompleted(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBadge = (confidence: number) => {
    const percentage = Math.round(confidence * 100);
    if (confidence >= 0.9) return <Badge variant="success" className="text-xs">{percentage}%</Badge>;
    if (confidence >= 0.7) return <Badge variant="warning" className="text-xs">{percentage}%</Badge>;
    return <Badge variant="error" className="text-xs">{percentage}%</Badge>;
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          🤖 Agentic Workflow Processing
        </h2>
        <p className="text-gray-600">
          AI agents working together to process your contract into a professional invoice
        </p>
        {contractName && (
          <Badge variant="primary" className="mt-2">
            {contractName}
          </Badge>
        )}
      </div>

      {/* Overall Progress */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Overall Progress</h3>
          <span className="text-sm text-gray-600">{Math.round(overallProgress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </Card>

      {/* Agent Steps - Modern Card Layout */}
      <div className="grid gap-6">
        {steps.map((step, index) => {
          const isActive = index === currentStepIndex;
          const isCompleted = step.status === 'completed';
          const isProcessing = step.status === 'processing';
          const needsInput = step.status === 'needs_input';
          
          return (
            <Card 
              key={step.id} 
              className={`
                relative overflow-hidden transition-all duration-500 transform
                ${isActive ? 'shadow-2xl scale-[1.02] ring-2 ring-blue-400 bg-gradient-to-br from-blue-50 to-indigo-50' : 
                  isCompleted ? 'shadow-md bg-gradient-to-br from-green-50 to-emerald-50 border-green-200' :
                  needsInput ? 'shadow-lg bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200 animate-pulse' :
                  'shadow-sm bg-white border-gray-200 hover:shadow-md'}
                ${index < currentStepIndex && !isCompleted ? 'opacity-75' : ''}
              `}
            >
              {/* Animated Background Gradient */}
              {isProcessing && (
                <div className="absolute inset-0 bg-gradient-to-r from-blue-400/10 to-purple-400/10 animate-gradient-x" />
              )}
              
              <div className="relative p-6">
                <div className="flex items-start space-x-4">
                  {/* Step Number & Icon */}
                  <div className="flex-shrink-0">
                    <div className={`
                      relative w-12 h-12 rounded-full flex items-center justify-center
                      ${isCompleted ? 'bg-green-500 text-white' :
                        isProcessing ? 'bg-blue-500 text-white animate-pulse' :
                        needsInput ? 'bg-yellow-500 text-white animate-bounce' :
                        'bg-gray-200 text-gray-500'}
                      transition-all duration-300
                    `}>
                      {isCompleted ? (
                        <CheckCircle className="h-6 w-6" />
                      ) : isProcessing ? (
                        <div className="relative">
                          <Loader2 className="h-6 w-6 animate-spin" />
                          <div className="absolute inset-0 animate-ping bg-blue-400 rounded-full opacity-20" />
                        </div>
                      ) : needsInput ? (
                        <User className="h-6 w-6 animate-pulse" />
                      ) : (
                        <span className="text-sm font-bold">{index + 1}</span>
                      )}
                    </div>
                  </div>

                  {/* Step Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className={`
                        text-xl font-semibold 
                        ${isActive ? 'text-blue-900' : 
                          isCompleted ? 'text-green-900' : 
                          needsInput ? 'text-yellow-900' : 'text-gray-700'}
                      `}>
                        {step.title}
                      </h3>
                      
                      <div className="flex items-center space-x-3">
                        {step.timestamp && (
                          <span className="text-xs text-gray-500 flex items-center bg-white/60 px-2 py-1 rounded-full">
                            <Clock className="h-3 w-3 mr-1" />
                            {step.timestamp}
                          </span>
                        )}
                        
                        <Badge 
                          className={`
                            font-medium
                            ${step.status === 'completed' ? 'bg-green-100 text-green-800 border-green-200' :
                              step.status === 'processing' ? 'bg-blue-100 text-blue-800 border-blue-200' :
                              step.status === 'needs_input' ? 'bg-yellow-100 text-yellow-800 border-yellow-200' :
                              'bg-gray-100 text-gray-700 border-gray-200'}
                          `}
                        >
                          {step.status === 'needs_input' ? '⚠️ Action Required' :
                           step.status === 'processing' ? '⚡ Processing' :
                           step.status === 'completed' ? '✅ Complete' : '⏳ Pending'}
                        </Badge>
                      </div>
                    </div>
                    
                    <p className={`
                      text-sm mb-4 leading-relaxed
                      ${isActive ? 'text-blue-700' : 
                        isCompleted ? 'text-green-700' : 
                        needsInput ? 'text-yellow-700' : 'text-gray-600'}
                    `}>
                      {step.description}
                    </p>

                    {/* Enhanced Progress Bar */}
                    {isProcessing && (
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-blue-700">Processing...</span>
                          <span className="text-xs text-blue-600">{step.progress}%</span>
                        </div>
                        <div className="w-full bg-blue-100 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500 relative"
                            style={{ width: `${step.progress}%` }}
                          >
                            <div className="absolute inset-0 bg-blue-300 animate-pulse opacity-50" />
                          </div>
                        </div>
                      </div>
                    )}

                  {/* Human Input Interface */}
                  {step.id === 'human_input' && (step.status === 'needs_input' || showHumanInputPopup) && validationFields.length > 0 && (
                    <div className="mt-4 space-y-4">
                      <div className="bg-white rounded-lg p-4 border border-yellow-200">
                        <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                          <Eye className="h-4 w-4 mr-2" />
                          Review & Correct Extracted Data
                        </h4>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {validationFields.map((field) => (
                            <div key={field.id} className="space-y-2">
                              <div className="flex items-center justify-between">
                                <label className="text-sm font-medium text-gray-700">
                                  {field.label}
                                  {field.required && <span className="text-red-500 ml-1">*</span>}
                                </label>
                                {getConfidenceBadge(field.confidence)}
                              </div>
                              
                              {isEditingField === field.id ? (
                                <div className="flex space-x-2">
                                  {field.type === 'textarea' ? (
                                    <Textarea
                                      value={editingValue}
                                      onChange={(e) => setEditingValue(e.target.value)}
                                      className="flex-1"
                                      rows={3}
                                    />
                                  ) : (
                                    <Input
                                      type={field.type === 'currency' ? 'number' : field.type}
                                      value={editingValue}
                                      onChange={(e) => setEditingValue(e.target.value)}
                                      className="flex-1"
                                    />
                                  )}
                                  <Button
                                    size="sm"
                                    onClick={() => handleFieldSave(field.id)}
                                    className="px-3"
                                  >
                                    <Save className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={handleFieldCancel}
                                    className="px-3"
                                  >
                                    <X className="h-4 w-4" />
                                  </Button>
                                </div>
                              ) : (
                                <div className="flex items-center space-x-2">
                                  <div className="flex-1 p-2 bg-gray-50 rounded border">
                                    <span className="text-sm">
                                      {field.type === 'currency' ? `$${field.value}` : field.value}
                                    </span>
                                  </div>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleFieldEdit(field.id)}
                                    className="px-3"
                                  >
                                    <Edit3 className="h-4 w-4" />
                                  </Button>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>

                        <div className="mt-6 flex justify-end">
                          <Button
                            onClick={handleCompleteHumanInput}
                            className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
                            disabled={validationFields.some(f => f.required && !f.validated && f.confidence < 0.9)}
                          >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            Confirm & Continue
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Show final invoice data */}
                  {step.id === 'invoice_generation' && step.status === 'completed' && (
                    <div className="mt-4">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <h4 className="font-medium text-green-800 mb-2">
                          ✅ Invoice Generated Successfully!
                        </h4>
                        <p className="text-sm text-green-700 mb-3">
                          Your professional invoice has been created with all validated data.
                        </p>
                        <div className="flex space-x-2">
                          <Button size="sm" variant="outline">
                            <Eye className="mr-2 h-4 w-4" />
                            Preview Invoice
                          </Button>
                          <Button size="sm">
                            <ArrowRight className="mr-2 h-4 w-4" />
                            Continue to Templates
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Card>
          );
        })}
      </div>

      {/* Status Footer */}
      <div className="text-center text-sm text-gray-500">
        {overallProgress === 100 ? (
          <span className="text-green-600 font-medium">
            🎉 Workflow completed successfully!
          </span>
        ) : (
          <span>
            AI agents are working... Step {currentStepIndex + 1} of {steps.length}
          </span>
        )}
      </div>
    </div>
  );
};

export default InteractiveAgenticFlow;