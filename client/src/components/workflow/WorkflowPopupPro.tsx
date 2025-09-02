import React, { useState, useEffect, useRef } from 'react';
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
  Target,
  Play,
  Clock,
  Zap,
  CheckCheck,
  AlertTriangle,
  Info,
  ArrowRight,
  Minimize2,
  Maximize2
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import HumanInputForm from './HumanInputForm';
import type { WorkflowEvent } from '../../services/websocketService';

interface WorkflowPopupProProps {
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
  estimatedTime?: number;
}

const WorkflowPopupPro: React.FC<WorkflowPopupProProps> = ({
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
      icon: <Brain className="h-5 w-5" />,
      description: 'Analyzing workflow requirements and coordinating agents',
      detailedDescription: 'The orchestrator analyzes your uploaded contract, determines the optimal processing strategy, and coordinates all other agents in the workflow pipeline.',
      status: 'pending',
      message: 'Initializing workflow...',
      estimatedTime: 15,
      substeps: [
        'Parsing contract file format',
        'Analyzing document structure and layout',
        'Planning optimal agent execution sequence',
        'Setting up workflow state management'
      ]
    },
    {
      id: 'contract_processing',
      name: 'contract_processing',
      displayName: 'Document Processing',
      icon: <FileText className="h-5 w-5" />,
      description: 'Extracting text and analyzing contract content with AI',
      detailedDescription: 'Advanced AI-powered processing extracts text using OCR, identifies key contract sections, and structures the data for validation.',
      status: 'pending',
      estimatedTime: 45,
      substeps: [
        'PDF text extraction and OCR processing',
        'Document structure and layout analysis',
        'Key section and clause identification',
        'Entity recognition and data extraction'
      ]
    },
    {
      id: 'validation',
      name: 'validation',
      displayName: 'Data Validation',
      icon: <Eye className="h-5 w-5" />,
      description: 'AI-powered validation and quality assurance',
      detailedDescription: 'Our intelligent validation system reviews extracted data for accuracy, completeness, and consistency. May require human input for complex cases.',
      status: 'pending',
      estimatedTime: 30,
      substeps: [
        'Data completeness and accuracy check',
        'Format validation and standardization',
        'Cross-reference verification',
        'Confidence scoring and quality assessment'
      ]
    },
    {
      id: 'correction',
      name: 'correction',
      displayName: 'Data Enhancement',
      icon: <Target className="h-5 w-5" />,
      description: 'Final data refinement and optimization',
      detailedDescription: 'Applies corrections, enhances data quality, and ensures all invoice fields are properly formatted and business-ready.',
      status: 'pending',
      estimatedTime: 20,
      substeps: [
        'Applying validation corrections',
        'Data normalization and formatting',
        'Field validation and standardization',
        'Final quality assurance check'
      ]
    },
    {
      id: 'ui_invoice_generator',
      name: 'ui_invoice_generator',
      displayName: 'Template Generation',
      icon: <Sparkles className="h-5 w-5" />,
      description: 'Creating professional React invoice templates',
      detailedDescription: 'Generates beautiful, customizable React invoice components with multiple design variations, ready for production use.',
      status: 'pending',
      estimatedTime: 25,
      substeps: [
        'Template design selection and customization',
        'React component code generation',
        'Style and branding integration',
        'Export preparation and optimization'
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
  const [startTime] = useState(Date.now());
  const [isMinimized, setIsMinimized] = useState(false);
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [showHumanInput, setShowHumanInput] = useState(false);
  
  const stepRefs = useRef<(HTMLDivElement | null)[]>([]);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Enhanced event handling with better matching
  useEffect(() => {
    updateStepsFromStatus();
  }, [workflowStatus, events]);

  // Auto-scroll to active step with smooth animation
  useEffect(() => {
    if (activeStepIndex >= 0 && stepRefs.current[activeStepIndex] && !isMinimized) {
      const element = stepRefs.current[activeStepIndex];
      const container = scrollContainerRef.current;
      
      if (element && container) {
        const elementTop = element.offsetTop;
        const containerHeight = container.clientHeight;
        const elementHeight = element.clientHeight;
        const scrollTop = elementTop - (containerHeight / 2) + (elementHeight / 2);
        
        container.scrollTo({
          top: scrollTop,
          behavior: 'smooth'
        });
      }
    }
  }, [activeStepIndex, isMinimized]);

  // Handle human input state
  useEffect(() => {
    setShowHumanInput(!!humanInputRequest);
    if (humanInputRequest) {
      setIsPaused(true);
    }
  }, [humanInputRequest]);

  const updateStepsFromStatus = () => {
    if (!workflowStatus && events.length === 0) return;

    const newSteps = [...steps];
    let newCurrentAgent = currentAgent;
    let newOverallProgress = overallProgress;
    let newQualityScore = qualityScore;
    let newConfidenceLevel = confidenceLevel;
    let newIsCompleted = false;
    let newHasError = false;
    let newIsPaused = isPaused;
    let newActiveStepIndex = activeStepIndex;

    // Process workflow status
    if (workflowStatus) {
      newCurrentAgent = workflowStatus.current_agent;
      newQualityScore = workflowStatus.quality_score;
      newConfidenceLevel = workflowStatus.confidence_level;

      const processingStatus = workflowStatus.processing_status || workflowStatus.status;
      
      if (processingStatus === 'completed' || processingStatus === 'success') {
        newIsCompleted = true;
        newOverallProgress = 100;
        newActiveStepIndex = newSteps.length - 1;
      } else if (processingStatus === 'failed' || processingStatus === 'error') {
        newHasError = true;
      } else if (processingStatus === 'needs_human_input') {
        newIsPaused = true;
        const validationIndex = newSteps.findIndex(s => s.id === 'validation');
        if (validationIndex >= 0) {
          newSteps[validationIndex].status = 'needs_input';
          newSteps[validationIndex].message = 'Human input required for validation';
          newActiveStepIndex = validationIndex;
        }
      }
    }

    // Process events with enhanced matching
    events.forEach(event => {
      const eventType = event.type;
      const eventData = event.data;
      
      switch (eventType) {
        case 'agent_transition':
        case 'agent_started':
        case 'status_update':
          if (eventData.current_agent) {
            newCurrentAgent = eventData.current_agent;
            
            const activeStepIdx = newSteps.findIndex(s => s.name === eventData.current_agent);
            if (activeStepIdx >= 0) {
              newSteps[activeStepIdx].status = 'active';
              newSteps[activeStepIdx].timestamp = event.timestamp;
              newSteps[activeStepIdx].message = eventData.message || 
                `${newSteps[activeStepIdx].displayName} is processing...`;
              
              newActiveStepIndex = activeStepIdx;
              
              // Mark previous steps as completed with smooth transitions
              for (let i = 0; i < activeStepIdx; i++) {
                if (newSteps[i].status !== 'completed') {
                  newSteps[i].status = 'completed';
                  newSteps[i].message = 'Completed successfully';
                  
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

        // Enhanced human input event handling
        case 'human_input_needed':
        case 'human_input_required':
          console.log('🚨 Human input required event received:', eventData);
          newIsPaused = true;
          const validationStep = newSteps.find(s => s.id === 'validation');
          if (validationStep) {
            validationStep.status = 'needs_input';
            validationStep.message = eventData.instructions || eventData.message || 'Human input required';
            newActiveStepIndex = newSteps.findIndex(s => s.id === 'validation');
          }
          break;

        case 'input_processed':
        case 'human_input_processed':
          newIsPaused = false;
          const validationStepProcessed = newSteps.find(s => s.id === 'validation');
          if (validationStepProcessed) {
            validationStepProcessed.status = 'completed';
            validationStepProcessed.message = 'Validation completed with human input';
          }
          break;

        case 'workflow_complete':
        case 'workflow_completed':
          newIsCompleted = true;
          newOverallProgress = 100;
          newSteps.forEach(step => {
            if (step.status === 'active' || step.status === 'pending') {
              step.status = 'completed';
              step.message = 'Completed successfully';
            }
          });
          newActiveStepIndex = newSteps.length - 1;
          break;

        case 'workflow_error':
        case 'error':
          newHasError = true;
          if (newCurrentAgent) {
            const errorStepIndex = newSteps.findIndex(s => s.name === newCurrentAgent);
            if (errorStepIndex >= 0) {
              newSteps[errorStepIndex].status = 'failed';
              newSteps[errorStepIndex].message = eventData.message || 'Step failed';
              newActiveStepIndex = errorStepIndex;
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
    setActiveStepIndex(newActiveStepIndex);
  };

  const getStepIcon = (step: AgentStep, index: number) => {
    const isActive = index === activeStepIndex;
    const baseClasses = "transition-all duration-300";
    
    switch (step.status) {
      case 'completed':
        return <CheckCircle className={`h-5 w-5 text-green-500 ${baseClasses}`} />;
      case 'active':
        return (
          <div className="relative">
            <Loader2 className={`h-5 w-5 text-blue-500 animate-spin ${baseClasses}`} />
            <div className="absolute inset-0 animate-ping">
              <Circle className="h-5 w-5 text-blue-300 opacity-75" />
            </div>
          </div>
        );
      case 'failed':
        return <AlertCircle className={`h-5 w-5 text-red-500 ${baseClasses}`} />;
      case 'needs_input':
        return (
          <div className="relative">
            <User className={`h-5 w-5 text-amber-500 ${baseClasses}`} />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-amber-400 rounded-full animate-pulse" />
          </div>
        );
      case 'paused':
        return <Pause className={`h-5 w-5 text-orange-500 ${baseClasses}`} />;
      default:
        return (
          <Circle className={`h-5 w-5 ${isActive ? 'text-blue-400' : 'text-gray-300'} ${baseClasses}`} />
        );
    }
  };

  const getStepStatusBadge = (status: string, isActive: boolean) => {
    const baseClasses = "text-xs font-medium transition-all duration-300";
    
    switch (status) {
      case 'completed':
        return (
          <Badge variant="success" className={`${baseClasses} animate-pulse`}>
            <CheckCheck className="w-3 h-3 mr-1" />
            Completed
          </Badge>
        );
      case 'active':
        return (
          <Badge variant="primary" className={`${baseClasses} animate-pulse shadow-lg`}>
            <Play className="w-3 h-3 mr-1" />
            Processing
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="error" className={baseClasses}>
            <AlertTriangle className="w-3 h-3 mr-1" />
            Failed
          </Badge>
        );
      case 'needs_input':
        return (
          <Badge variant="warning" className={`${baseClasses} animate-bounce shadow-md`}>
            <User className="w-3 h-3 mr-1" />
            Input Required
          </Badge>
        );
      case 'paused':
        return (
          <Badge variant="secondary" className={baseClasses}>
            <Pause className="w-3 h-3 mr-1" />
            Paused
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className={baseClasses}>
            <Clock className="w-3 h-3 mr-1" />
            Waiting
          </Badge>
        );
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
    
    // Use estimated times from step definitions
    const remainingEstimatedTime = steps
      .filter((_, index) => index >= activeStepIndex)
      .reduce((sum, step) => sum + (step.estimatedTime || 30), 0);
    
    return remainingEstimatedTime;
  };

  const getOverallStatusColor = () => {
    if (hasError) return 'from-red-500 to-red-600';
    if (isCompleted) return 'from-green-500 to-green-600';
    if (isPaused) return 'from-amber-500 to-amber-600';
    return 'from-blue-500 to-purple-600';
  };

  const getProgressBarColor = () => {
    if (hasError) return 'bg-red-500';
    if (isCompleted) return 'bg-green-500';
    if (isPaused) return 'bg-amber-500';
    return 'bg-gradient-to-r from-blue-500 to-purple-600';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className={`w-full max-w-5xl transition-all duration-500 shadow-2xl border-0 ${
        isMinimized ? 'max-h-32' : 'max-h-[90vh]'
      } overflow-hidden`}>
        
        {/* Header */}
        <CardHeader className={`border-b bg-gradient-to-r ${getOverallStatusColor()} text-white relative overflow-hidden`}>
          {/* Animated background pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-white/10" />
            <div className="absolute top-0 left-0 w-full h-full opacity-20" style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='m36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
            }} />
          </div>
          
          <div className="relative z-10">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                  <Brain className="h-6 w-6 text-white" />
                </div>
                <div>
                  <CardTitle className="text-xl font-bold text-white flex items-center">
                    AI Contract Processing Pipeline
                    {isCompleted && <CheckCircle className="h-5 w-5 ml-2 animate-bounce" />}
                    {hasError && <AlertCircle className="h-5 w-5 ml-2 animate-pulse" />}
                    {isPaused && <Pause className="h-5 w-5 ml-2 animate-pulse" />}
                  </CardTitle>
                  <p className="text-white/90 text-sm mt-1 font-medium">
                    Processing: {contractName}
                  </p>
                  <p className="text-white/70 text-xs">
                    Workflow ID: {workflowId}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                {/* Status indicators */}
                {isCompleted && (
                  <div className="flex items-center bg-green-500/20 text-green-100 px-3 py-1 rounded-full backdrop-blur-sm">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    <span className="text-sm font-medium">Complete!</span>
                  </div>
                )}
                {hasError && (
                  <div className="flex items-center bg-red-500/20 text-red-100 px-3 py-1 rounded-full backdrop-blur-sm">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    <span className="text-sm font-medium">Error</span>
                  </div>
                )}
                {isPaused && (
                  <div className="flex items-center bg-amber-500/20 text-amber-100 px-3 py-1 rounded-full backdrop-blur-sm">
                    <Pause className="h-4 w-4 mr-1" />
                    <span className="text-sm font-medium">Paused</span>
                  </div>
                )}
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="text-white/80 hover:text-white hover:bg-white/20 transition-colors"
                >
                  {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="text-white/80 hover:text-white hover:bg-white/20 transition-colors"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Overall Progress */}
            {!isMinimized && (
              <div className="mt-6">
                <div className="flex items-center justify-between text-sm text-white/90 mb-3">
                  <div className="flex items-center space-x-4">
                    <span className="font-semibold">Progress: {overallProgress}%</span>
                    {qualityScore !== null && (
                      <span className="flex items-center">
                        <Zap className="w-4 h-4 mr-1" />
                        Quality: {(qualityScore * 100).toFixed(0)}%
                      </span>
                    )}
                    {confidenceLevel !== null && (
                      <span className="flex items-center">
                        <Target className="w-4 h-4 mr-1" />
                        Confidence: {(confidenceLevel * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {getTimeEstimate() && !isCompleted && (
                      <span className="flex items-center bg-white/10 px-2 py-1 rounded-lg backdrop-blur-sm">
                        <Clock className="w-3 h-3 mr-1" />
                        ETA: {Math.ceil(getTimeEstimate() / 60)}m
                      </span>
                    )}
                    <span className="text-xs bg-white/10 px-2 py-1 rounded-lg backdrop-blur-sm">
                      {steps.filter(s => s.status === 'completed').length} / {steps.length} steps
                    </span>
                  </div>
                </div>
                
                <div className="relative w-full bg-white/20 rounded-full h-4 overflow-hidden backdrop-blur-sm">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 relative ${getProgressBarColor()}`}
                    style={{ width: `${overallProgress}%` }}
                  >
                    {/* Animated shimmer effect */}
                    {!isCompleted && !hasError && (
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse" />
                    )}
                    {/* Completion celebration effect */}
                    {isCompleted && (
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-bounce" />
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardHeader>

        {/* Content */}
        {!isMinimized && (
          <CardContent className="p-0 bg-gradient-to-br from-slate-50 to-gray-100">
            <div className="max-h-[60vh] overflow-y-auto" ref={scrollContainerRef}>
              
              {/* Human Input Form */}
              {showHumanInput && humanInputRequest && onSubmitHumanInput && onCancelHumanInput && (
                <div className="p-6 bg-gradient-to-r from-amber-50 to-orange-50 border-b-2 border-amber-200">
                  <div className="mb-4 text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-amber-100 rounded-full mb-3">
                      <User className="w-8 h-8 text-amber-600 animate-pulse" />
                    </div>
                    <h3 className="text-lg font-semibold text-amber-800 mb-2">
                      Human Input Required
                    </h3>
                    <p className="text-amber-700 text-sm">
                      Our AI needs your expertise to ensure perfect accuracy
                    </p>
                  </div>
                  
                  <HumanInputForm
                    request={humanInputRequest}
                    onSubmit={(fieldValues, userNotes) => {
                      onSubmitHumanInput(fieldValues, userNotes);
                      setShowHumanInput(false);
                    }}
                    onCancel={() => {
                      onCancelHumanInput();
                      setShowHumanInput(false);
                    }}
                  />
                </div>
              )}

              {/* Agent Steps */}
              <div className="p-6 space-y-6">
                {steps.map((step, index) => {
                  const isActive = index === activeStepIndex;
                  const isCurrentOrPast = index <= activeStepIndex;
                  
                  return (
                    <div
                      key={step.id}
                      ref={(el) => stepRefs.current[index] = el}
                      className={`relative transition-all duration-700 transform ${
                        isActive 
                          ? 'scale-105 shadow-lg ring-2 ring-blue-500 ring-opacity-50 rounded-xl p-6 bg-gradient-to-r from-blue-50 to-indigo-50' 
                          : step.status === 'completed' 
                            ? 'bg-green-50/50 rounded-lg p-4' 
                            : step.status === 'failed'
                              ? 'bg-red-50/50 rounded-lg p-4'
                              : 'p-4 hover:bg-gray-50/50 rounded-lg'
                      }`}
                    >
                      {/* Connection line */}
                      {index < steps.length - 1 && (
                        <div className={`absolute left-8 ${isActive ? 'top-20' : 'top-16'} w-0.5 h-12 transition-colors duration-500 ${
                          isCurrentOrPast ? 'bg-gradient-to-b from-blue-400 to-blue-300' : 'bg-gray-200'
                        }`} />
                      )}

                      <div className="flex items-start space-x-4">
                        {/* Step Icon with enhanced styling */}
                        <div className={`flex-shrink-0 relative transition-transform duration-300 ${
                          isActive ? 'transform scale-110' : ''
                        }`}>
                          <div className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-500 ${
                            step.status === 'completed' 
                              ? 'bg-gradient-to-br from-green-400 to-green-500 shadow-lg' :
                            step.status === 'active' 
                              ? 'bg-gradient-to-br from-blue-400 to-blue-500 shadow-lg shadow-blue-200' :
                            step.status === 'failed' 
                              ? 'bg-gradient-to-br from-red-400 to-red-500 shadow-lg' :
                            step.status === 'needs_input' 
                              ? 'bg-gradient-to-br from-amber-400 to-amber-500 shadow-lg shadow-amber-200' :
                            'bg-gradient-to-br from-gray-200 to-gray-300'
                          }`}>
                            <div className="text-white">
                              {step.status === 'completed' ? step.icon : step.status === 'active' ? (
                                <div className="relative">
                                  {step.icon}
                                  <div className="absolute inset-0 animate-ping">
                                    <Circle className="h-5 w-5 text-white opacity-60" />
                                  </div>
                                </div>
                              ) : getStepIcon(step, index)}
                            </div>
                          </div>
                          
                          {/* Step number badge */}
                          <div className={`absolute -top-1 -right-1 w-7 h-7 bg-white border-2 rounded-full flex items-center justify-center text-xs font-bold transition-colors duration-500 ${
                            step.status === 'completed' ? 'border-green-400 text-green-600' :
                            step.status === 'active' ? 'border-blue-400 text-blue-600 shadow-md' :
                            step.status === 'failed' ? 'border-red-400 text-red-600' :
                            step.status === 'needs_input' ? 'border-amber-400 text-amber-600' :
                            'border-gray-300 text-gray-500'
                          }`}>
                            {index + 1}
                          </div>
                        </div>

                        {/* Step Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className={`font-semibold flex items-center transition-colors duration-300 ${
                              isActive ? 'text-lg text-blue-800' : 'text-base text-gray-900'
                            }`}>
                              <span className="mr-2">{step.displayName}</span>
                              {step.status === 'active' && (
                                <ArrowRight className="w-4 h-4 text-blue-500 animate-pulse ml-2" />
                              )}
                            </h4>
                            {getStepStatusBadge(step.status, isActive)}
                          </div>

                          <p className={`text-sm mb-3 transition-colors duration-300 ${
                            isActive ? 'text-blue-700' : 'text-gray-600'
                          }`}>
                            {isActive ? step.detailedDescription : step.description}
                          </p>

                          {/* Current status message */}
                          {step.message && (
                            <div className={`text-sm font-medium mb-3 p-3 rounded-lg transition-all duration-300 ${
                              step.status === 'active' 
                                ? 'bg-blue-100 text-blue-700 border border-blue-200' :
                              step.status === 'completed' 
                                ? 'bg-green-100 text-green-700 border border-green-200' :
                              step.status === 'failed' 
                                ? 'bg-red-100 text-red-700 border border-red-200' :
                              step.status === 'needs_input' 
                                ? 'bg-amber-100 text-amber-700 border border-amber-200 animate-pulse' :
                              'bg-gray-100 text-gray-600'
                            }`}>
                              <div className="flex items-center">
                                <Info className="w-4 h-4 mr-2 flex-shrink-0" />
                                {step.message}
                              </div>
                            </div>
                          )}

                          {/* Substeps for active step */}
                          {step.status === 'active' && step.substeps && (
                            <div className="mt-4 space-y-2 bg-white/50 p-4 rounded-lg border border-blue-100">
                              <h5 className="text-xs font-semibold text-blue-800 mb-3 uppercase tracking-wide">
                                Current Operations
                              </h5>
                              {step.substeps.map((substep, subIndex) => (
                                <div key={subIndex} className="flex items-center text-xs text-blue-700">
                                  <div className="w-2 h-2 bg-blue-400 rounded-full mr-3 animate-pulse flex-shrink-0" />
                                  <span>{substep}</span>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Progress bar for active step */}
                          {step.status === 'active' && step.progress !== undefined && (
                            <div className="mt-4">
                              <div className="flex items-center justify-between text-xs text-blue-600 mb-2">
                                <span>Step Progress</span>
                                <span>{step.progress}%</span>
                              </div>
                              <div className="w-full bg-blue-100 rounded-full h-2 overflow-hidden">
                                <div
                                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-700"
                                  style={{ width: `${step.progress}%` }}
                                />
                              </div>
                            </div>
                          )}

                          {/* Timestamp and duration */}
                          <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                            <div className="flex items-center space-x-4">
                              {step.timestamp && (
                                <span className="flex items-center">
                                  <Clock className="w-3 h-3 mr-1" />
                                  Started: {new Date(step.timestamp).toLocaleTimeString()}
                                </span>
                              )}
                              {step.duration && (
                                <span className="bg-gray-100 px-2 py-1 rounded-lg">
                                  Duration: {formatDuration(step.duration)}
                                </span>
                              )}
                            </div>
                            
                            {step.status === 'pending' && step.estimatedTime && (
                              <span className="text-blue-500 bg-blue-50 px-2 py-1 rounded-lg">
                                ~{step.estimatedTime}s estimated
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Footer Actions */}
            <div className="border-t bg-white p-6">
              {isCompleted && (
                <div className="text-center space-y-4">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-400 to-green-500 rounded-full mb-4">
                    <CheckCircle className="h-10 w-10 text-white" />
                  </div>
                  
                  <div>
                    <h3 className="text-xl font-bold text-green-700 mb-2">
                      🎉 Processing Complete!
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Your contract has been successfully processed and professional invoice templates are ready for use.
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-md mx-auto">
                    {onDownloadData && (
                      <Button
                        onClick={onDownloadData}
                        variant="outline"
                        className="flex items-center justify-center hover:shadow-md transition-shadow"
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download Data
                      </Button>
                    )}
                    
                    {onViewTemplates && (
                      <Button
                        onClick={onViewTemplates}
                        variant="primary"
                        className="flex items-center justify-center bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all"
                      >
                        <ExternalLink className="mr-2 h-4 w-4" />
                        View Templates
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {hasError && (
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-red-400 to-red-500 rounded-full mb-4">
                    <AlertCircle className="h-8 w-8 text-white" />
                  </div>
                  
                  <h3 className="text-lg font-semibold text-red-700 mb-2">
                    Processing Failed
                  </h3>
                  <p className="text-gray-600 mb-4">
                    An error occurred during processing. Please try again or contact support.
                  </p>
                  
                  <div className="flex gap-3 justify-center">
                    <Button variant="outline" onClick={onClose}>
                      Close
                    </Button>
                    <Button variant="primary" onClick={() => window.location.reload()}>
                      Try Again
                    </Button>
                  </div>
                </div>
              )}

              {!isCompleted && !hasError && (
                <div className="flex justify-between items-center">
                  <div className="flex items-center text-sm text-gray-600 space-x-4">
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-2" />
                      Processing your contract...
                    </div>
                    {isPaused && (
                      <div className="flex items-center text-amber-600">
                        <Pause className="w-4 h-4 mr-1" />
                        Workflow paused for input
                      </div>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setIsMinimized(true)}
                    >
                      <Minimize2 className="w-4 h-4 mr-2" />
                      Minimize
                    </Button>
                    <Button variant="outline" size="sm" onClick={onClose}>
                      Close
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
};

export default WorkflowPopupPro;