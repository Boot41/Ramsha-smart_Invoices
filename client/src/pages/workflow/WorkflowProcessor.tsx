import React, { useState, useCallback, useEffect } from 'react';
import { Upload, FileText, Zap, Settings, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { workflowAPI, WorkflowResponse } from '../../services/workflowService';
import { workflowWebSocket, WorkflowEvent } from '../../services/websocketService';
import WorkflowStatusTracker from '../../components/workflow/WorkflowStatusTracker';
import HumanInputForm from '../../components/workflow/HumanInputForm';

interface FileUpload {
  file: File;
  preview?: string;
  error?: string;
}

const WorkflowProcessor: React.FC = () => {
  // File upload state
  const [selectedFile, setSelectedFile] = useState<FileUpload | null>(null);
  const [contractName, setContractName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [processingMessage, setProcessingMessage] = useState<string>('');
  const [processingStep, setProcessingStep] = useState<string>('');
  
  // Workflow state
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowResponse | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<any>(null);
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([]);
  const [showHumanInput, setShowHumanInput] = useState(false);
  const [humanInputRequest, setHumanInputRequest] = useState<any>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [pauseReason, setPauseReason] = useState<string>('');
  
  // WebSocket connection state
  const [wsConnected, setWsConnected] = useState(false);
  const [wsError, setWsError] = useState<string | null>(null);

  // File handling
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      setSelectedFile({
        file,
        error: 'Please select a PDF, JPG, or PNG file'
      });
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setSelectedFile({
        file,
        error: 'File size must be less than 10MB'
      });
      return;
    }

    setSelectedFile({ file });
    
    // Auto-generate contract name if not set
    if (!contractName) {
      const baseName = file.name.replace(/\.[^/.]+$/, '');
      setContractName(baseName);
    }
  }, [contractName]);

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
  }, []);

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      handleFileSelect({ target: { files: [file] } } as any);
    }
  }, [handleFileSelect]);

  // Start workflow
  const startWorkflow = async () => {
    if (!selectedFile?.file || !contractName.trim()) {
      setUploadError('Please select a file and enter a contract name');
      return;
    }

    if (selectedFile.error) {
      setUploadError(selectedFile.error);
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setProcessingMessage('🚀 Starting workflow...');
    setProcessingStep('Initializing');

    try {
      const userId = workflowAPI.getCurrentUserId();
      
      setProcessingMessage('📤 Uploading contract...');
      setProcessingStep('Uploading');
      
      const response = await workflowAPI.startWorkflow(
        selectedFile.file,
        contractName.trim(),
        userId,
        {
          source: 'web_ui',
          timestamp: new Date().toISOString()
        }
      );

      console.log('🚀 Workflow started:', response);
      setCurrentWorkflow(response);
      
      setProcessingMessage('🔗 Connecting to workflow...');
      setProcessingStep('Connecting');
      
      // Connect to WebSocket for real-time updates
      if (response.workflow_id) {
        await connectToWorkflow(response.workflow_id);
        setProcessingMessage('✅ Connected! Agents starting...');
        setProcessingStep('Processing');
      }
      
    } catch (error) {
      console.error('❌ Failed to start workflow:', error);
      setUploadError(error instanceof Error ? error.message : 'Failed to start workflow');
      setProcessingMessage('');
      setProcessingStep('');
    } finally {
      // Don't set isUploading to false immediately - let workflow events handle it
    }
  };

  // Connect to workflow WebSocket
  const connectToWorkflow = async (workflowId: string) => {
    try {
      const connected = await workflowWebSocket.connect(workflowId);
      if (connected) {
        setWsConnected(true);
        setWsError(null);
      } else {
        setWsError('Failed to connect to workflow updates');
      }
    } catch (error) {
      console.error('❌ WebSocket connection error:', error);
      setWsError('Connection error');
    }
  };

  // Setup WebSocket event listeners
  useEffect(() => {
    const handleStatusUpdate = (event: WorkflowEvent) => {
      console.log('📊 Status update:', event.data);
      setWorkflowStatus(event.data);
      setWorkflowEvents(prev => [...prev, event]);
      
      // Update processing messages based on current agent
      if (event.data.current_agent) {
        const agentMessages = {
          'orchestrator': '🎯 Orchestrating workflow...',
          'contract_processing': '📄 Processing contract document...',
          'validation': '🔍 Validating extracted data...',
          'correction': '✏️ Applying corrections...',
          'ui_invoice_generator': '🎨 Generating invoice template...'
        };
        
        const message = event.data.message || agentMessages[event.data.current_agent] || `Processing with ${event.data.current_agent}...`;
        setProcessingMessage(message);
        setProcessingStep(event.data.current_agent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()));
      }
    };

    const handleHumanInputNeeded = (event: WorkflowEvent) => {
      console.log('🤔 Human input needed:', event.data);
      setHumanInputRequest(event.data);
      setShowHumanInput(true);
      setIsPaused(true);
      setPauseReason('Waiting for human input');
      setProcessingMessage('⏸️ Human input required');
      setProcessingStep('Paused for Review');
      setWorkflowEvents(prev => [...prev, event]);
    };

    const handleInputProcessed = (event: WorkflowEvent) => {
      console.log('✅ Input processed:', event.data);
      setShowHumanInput(false);
      setHumanInputRequest(null);
      setIsPaused(false);
      setPauseReason('');
      setProcessingMessage('▶️ Resuming workflow...');
      setProcessingStep('Resuming');
      setWorkflowEvents(prev => [...prev, event]);
    };
    
    const handleWorkflowPaused = (event: WorkflowEvent) => {
      console.log('⏸️ Workflow paused:', event.data);
      setIsPaused(true);
      setPauseReason(event.data.reason || 'Workflow paused');
      setWorkflowEvents(prev => [...prev, event]);
    };

    const handleWorkflowResumed = (event: WorkflowEvent) => {
      console.log('▶️ Workflow resumed:', event.data);
      setIsPaused(false);
      setPauseReason('');
      setWorkflowEvents(prev => [...prev, event]);
    };

    const handleWorkflowComplete = (event: WorkflowEvent) => {
      console.log('🎉 Workflow complete:', event.data);
      setIsUploading(false);
      setProcessingMessage('🎉 Workflow completed successfully!');
      setProcessingStep('Completed');
      setWorkflowEvents(prev => [...prev, event]);
    };

    const handleError = (event: WorkflowEvent) => {
      console.error('❌ Workflow error:', event.data);
      setWsError(event.data.message || 'Workflow error occurred');
      setIsUploading(false);
      setProcessingMessage('❌ Workflow failed');
      setProcessingStep('Error');
      setWorkflowEvents(prev => [...prev, event]);
    };

    const handleConnectionEstablished = (event: WorkflowEvent) => {
      console.log('🔌 WebSocket connected:', event.data);
      setWsConnected(true);
      setWsError(null);
    };

    const handleConnectionClosed = (event: WorkflowEvent) => {
      console.log('🔌 WebSocket disconnected:', event.data);
      setWsConnected(false);
    };

    // Register event listeners
    workflowWebSocket.on('status_update', handleStatusUpdate);
    workflowWebSocket.on('human_input_needed', handleHumanInputNeeded);
    workflowWebSocket.on('input_processed', handleInputProcessed);
    workflowWebSocket.on('workflow_paused', handleWorkflowPaused);
    workflowWebSocket.on('workflow_resumed', handleWorkflowResumed);
    workflowWebSocket.on('workflow_complete', handleWorkflowComplete);
    workflowWebSocket.on('error', handleError);
    workflowWebSocket.on('connection_established', handleConnectionEstablished);
    workflowWebSocket.on('connection_closed', handleConnectionClosed);

    return () => {
      // Cleanup event listeners
      workflowWebSocket.off('status_update', handleStatusUpdate);
      workflowWebSocket.off('human_input_needed', handleHumanInputNeeded);
      workflowWebSocket.off('input_processed', handleInputProcessed);
      workflowWebSocket.off('workflow_paused', handleWorkflowPaused);
      workflowWebSocket.off('workflow_resumed', handleWorkflowResumed);
      workflowWebSocket.off('workflow_complete', handleWorkflowComplete);
      workflowWebSocket.off('error', handleError);
      workflowWebSocket.off('connection_established', handleConnectionEstablished);
      workflowWebSocket.off('connection_closed', handleConnectionClosed);
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      workflowWebSocket.disconnect();
    };
  }, []);

  const resetWorkflow = () => {
    setCurrentWorkflow(null);
    setWorkflowStatus(null);
    setWorkflowEvents([]);
    setShowHumanInput(false);
    setHumanInputRequest(null);
    setSelectedFile(null);
    setContractName('');
    setUploadError(null);
    setIsUploading(false);
    setProcessingMessage('');
    setProcessingStep('');
    setIsPaused(false);
    setPauseReason('');
    workflowWebSocket.disconnect();
    setWsConnected(false);
    setWsError(null);
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🤖 Agentic Workflow Processor
        </h1>
        <p className="text-gray-600">
          Upload a contract and let our AI agents automatically process it into a professional invoice
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Upload & Controls */}
        <div className="space-y-6">
          
          {/* File Upload Card */}
          {!currentWorkflow && (
            <Card className="p-6">
              <div className="mb-4">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  📄 Upload Contract
                </h2>
                <p className="text-sm text-gray-600">
                  Upload a PDF, JPG, or PNG file of your contract or rental agreement
                </p>
              </div>

              {/* Drag & Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                  selectedFile?.error
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-300 hover:border-blue-400 bg-gray-50'
                }`}
              >
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileSelect}
                />
                
                {selectedFile ? (
                  <div className="space-y-2">
                    <FileText className="mx-auto h-12 w-12 text-blue-500" />
                    <p className="text-sm font-medium text-gray-900">
                      {selectedFile.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(selectedFile.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    {selectedFile.error && (
                      <p className="text-xs text-red-600 mt-2">
                        {selectedFile.error}
                      </p>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedFile(null)}
                      className="mt-2"
                    >
                      Remove File
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div>
                      <label
                        htmlFor="file-upload"
                        className="cursor-pointer text-blue-600 hover:text-blue-500"
                      >
                        Click to upload
                      </label>
                      <span className="text-gray-500"> or drag and drop</span>
                    </div>
                    <p className="text-xs text-gray-500">
                      PDF, JPG, PNG up to 10MB
                    </p>
                  </div>
                )}
              </div>

              {/* Contract Name Input */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Contract Name
                </label>
                <Input
                  type="text"
                  placeholder="e.g., Apartment Lease Agreement 2024"
                  value={contractName}
                  onChange={(e) => setContractName(e.target.value)}
                  className="w-full"
                />
              </div>

              {/* Upload Error */}
              {uploadError && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-center">
                    <AlertCircle className="h-4 w-4 text-red-500 mr-2" />
                    <p className="text-sm text-red-700">{uploadError}</p>
                  </div>
                </div>
              )}

              {/* Start Button with Real-time Processing */}
              <Button
                onClick={startWorkflow}
                disabled={!selectedFile?.file || !contractName.trim() || isUploading || !!selectedFile?.error}
                className="w-full mt-4"
                size="lg"
              >
                {isUploading ? (
                  <div className="flex flex-col items-center space-y-1">
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      {processingMessage || 'Processing...'}
                    </div>
                    {processingStep && (
                      <span className="text-xs opacity-80">
                        Step: {processingStep}
                      </span>
                    )}
                  </div>
                ) : (
                  <>
                    <Zap className="mr-2 h-4 w-4" />
                    Start Agentic Processing
                  </>
                )}
              </Button>
              
              {/* Processing Status Card (shown during workflow) */}
              {isUploading && currentWorkflow && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-semibold text-blue-900">
                      🔄 Processing Status
                    </h4>
                    <div className="flex items-center space-x-2">
                      <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full" />
                      <span className="text-xs text-blue-700">Active</span>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center text-sm text-blue-800">
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-2" />
                      {processingMessage}
                    </div>
                    
                    {processingStep && (
                      <div className="text-xs text-blue-600">
                        Current Step: <span className="font-medium">{processingStep}</span>
                      </div>
                    )}
                    
                    {/* Processing animation */}
                    <div className="mt-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
                      </div>
                    </div>
                    
                    {/* Progress hint */}
                    <div className="text-xs text-blue-500 mt-1 opacity-70">
                      {isPaused ? '⏸️ Waiting for input' : '🔄 Agents are working...'}
                    </div>
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Workflow Summary Card */}
          {currentWorkflow && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  🚀 Active Workflow
                </h2>
                <div className="flex space-x-2">
                  <Badge variant={wsConnected ? 'success' : 'secondary'}>
                    {wsConnected ? '🔗 Connected' : '⚠️ Disconnected'}
                  </Badge>
                  {isPaused && (
                    <Badge variant="warning">
                      ⏸️ Paused
                    </Badge>
                  )}
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">Workflow ID:</p>
                  <p className="text-xs font-mono text-gray-600 bg-gray-100 px-2 py-1 rounded">
                    {currentWorkflow.workflow_id}
                  </p>
                </div>
                
                <div>
                  <p className="text-sm font-medium text-gray-700">Contract:</p>
                  <p className="text-sm text-gray-600">{contractName}</p>
                </div>
                
                <div>
                  <p className="text-sm font-medium text-gray-700">Status:</p>
                  <Badge variant="primary">{currentWorkflow.status}</Badge>
                  {isPaused && pauseReason && (
                    <p className="text-xs text-yellow-600 mt-1">
                      {pauseReason}
                    </p>
                  )}
                </div>

                {wsError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-xs text-red-700">WebSocket Error: {wsError}</p>
                  </div>
                )}
              </div>

              <Button
                onClick={resetWorkflow}
                variant="outline"
                className="w-full mt-4"
              >
                Start New Workflow
              </Button>
            </Card>
          )}

        </div>

        {/* Right Column - Status & Progress */}
        <div className="space-y-6">
          
          {/* Workflow Status Tracker */}
          {currentWorkflow && (
            <WorkflowStatusTracker
              workflowId={currentWorkflow.workflow_id}
              workflowStatus={workflowStatus}
              events={workflowEvents}
            />
          )}

          {/* Human Input Form */}
          {showHumanInput && humanInputRequest && (
            <HumanInputForm
              request={humanInputRequest}
              onSubmit={(fieldValues, userNotes) => {
                workflowWebSocket.submitHumanInput(fieldValues, userNotes);
              }}
              onCancel={() => setShowHumanInput(false)}
            />
          )}

          {/* Getting Started */}
          {!currentWorkflow && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                🎯 How It Works
              </h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">1</div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Upload Contract</p>
                    <p className="text-xs text-gray-600">Upload your rental agreement or contract file</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">2</div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">AI Processing</p>
                    <p className="text-xs text-gray-600">Our agents extract data and validate information</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">3</div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Review & Correct</p>
                    <p className="text-xs text-gray-600">Review and correct any extracted data</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">4</div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Generate Invoice</p>
                    <p className="text-xs text-gray-600">Get a professional invoice template</p>
                  </div>
                </div>
              </div>
            </Card>
          )}
          
        </div>
      </div>
    </div>
  );
};

export default WorkflowProcessor;