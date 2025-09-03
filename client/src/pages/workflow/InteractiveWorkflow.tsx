import React, { useState, useEffect } from 'react';
import { Upload, FileText, ArrowLeft, RefreshCw } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import InteractiveAgenticFlow from '../../components/workflow/InteractiveAgenticFlow';
import { workflowAPI } from '../../services/workflowService';
import { workflowWebSocket } from '../../services/websocketService';
import type { WorkflowResponse } from '../../services/workflowService';
import type { WorkflowEvent } from '../../services/websocketService';

interface FileUpload {
  file: File;
  preview?: string;
  error?: string;
}

const InteractiveWorkflow: React.FC = () => {
  // Upload state
  const [selectedFile, setSelectedFile] = useState<FileUpload | null>(null);
  const [contractName, setContractName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Workflow state
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowResponse | null>(null);
  const [workflowStarted, setWorkflowStarted] = useState(false);
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  
  // Human input state
  const [humanInputData, setHumanInputData] = useState<any>(null);
  const [showHumanInputPopup, setShowHumanInputPopup] = useState(false);

  // File handling
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
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
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      handleFileSelect({ target: { files: [file] } } as any);
    }
  };

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

    try {
      let userId: string;
      try {
        userId = workflowAPI.getCurrentUserId();
        console.log('🔍 Using user ID for workflow:', userId);
      } catch (error) {
        console.error('❌ Failed to get user ID:', error);
        setUploadError('Please log in again to start a workflow');
        return;
      }
      
      const response = await workflowAPI.startWorkflow(
        selectedFile.file,
        contractName.trim(),
        userId,
        {
          source: 'interactive_ui',
          timestamp: new Date().toISOString()
        }
      );

      console.log('🚀 Interactive workflow started:', response);
      setCurrentWorkflow(response);
      setWorkflowStarted(true);
      
      // Connect to WebSocket for real-time updates
      if (response.workflow_id) {
        await connectToWorkflow(response.workflow_id);
      }
      
    } catch (error) {
      console.error('❌ Failed to start workflow:', error);
      setUploadError(error instanceof Error ? error.message : 'Failed to start workflow');
    } finally {
      setIsUploading(false);
    }
  };

  // Connect to workflow WebSocket
  const connectToWorkflow = async (workflowId: string) => {
    try {
      const connected = await workflowWebSocket.connect(workflowId);
      if (connected) {
        setWsConnected(true);
      }
    } catch (error) {
      console.error('❌ WebSocket connection error:', error);
    }
  };

  // WebSocket event handlers
  useEffect(() => {
    const handleWorkflowEvent = (event: WorkflowEvent) => {
      setWorkflowEvents(prev => [...prev, event]);
    };

    const handleHumanInputNeeded = (event: WorkflowEvent) => {
      console.log('🙋 Human input needed event received:', event.data);
      setHumanInputData(event.data);
      setShowHumanInputPopup(true);
      setWorkflowEvents(prev => [...prev, event]);
    };

    const handleInputProcessed = (event: WorkflowEvent) => {
      console.log('✅ Human input processed:', event.data);
      setShowHumanInputPopup(false);
      setHumanInputData(null);
      setWorkflowEvents(prev => [...prev, event]);
    };

    // Register event listeners
    workflowWebSocket.on('status_update', handleWorkflowEvent);
    workflowWebSocket.on('agent_change', handleWorkflowEvent);
    workflowWebSocket.on('human_input_needed', handleHumanInputNeeded);
    workflowWebSocket.on('input_processed', handleInputProcessed);
    workflowWebSocket.on('workflow_complete', handleWorkflowEvent);
    workflowWebSocket.on('workflow_error', handleWorkflowEvent);
    workflowWebSocket.on('connection_established', () => setWsConnected(true));
    workflowWebSocket.on('connection_closed', () => setWsConnected(false));

    return () => {
      // Cleanup event listeners
      workflowWebSocket.off('status_update', handleWorkflowEvent);
      workflowWebSocket.off('agent_change', handleWorkflowEvent);
      workflowWebSocket.off('human_input_needed', handleHumanInputNeeded);
      workflowWebSocket.off('input_processed', handleInputProcessed);
      workflowWebSocket.off('workflow_complete', handleWorkflowEvent);
      workflowWebSocket.off('workflow_error', handleWorkflowEvent);
    };
  }, []);

  // Handle step completion
  const handleStepComplete = (stepId: string, data?: any) => {
    console.log(`Step ${stepId} completed:`, data);
    // Handle specific step completions if needed
  };

  // Handle workflow completion
  const handleWorkflowComplete = (finalData: any) => {
    console.log('Workflow completed with data:', finalData);
    // Navigate to final results or show success message
  };

  // Reset workflow
  const resetWorkflow = () => {
    setCurrentWorkflow(null);
    setWorkflowStarted(false);
    setWorkflowEvents([]);
    setSelectedFile(null);
    setContractName('');
    setUploadError(null);
    setIsUploading(false);
    workflowWebSocket.disconnect();
    setWsConnected(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto p-6 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            🤖 Interactive Agentic Workflow
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience AI agents working together in real-time to transform your contracts into professional invoices
          </p>
        </div>

        {!workflowStarted ? (
          /* Upload Interface */
          <div className="max-w-2xl mx-auto">
            <Card className="p-8 shadow-lg border-0 bg-white/70 backdrop-blur-sm">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Upload Your Contract
                </h2>
                <p className="text-gray-600">
                  Start by uploading a contract document to begin the agentic processing
                </p>
              </div>

              {/* Drag & Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                  selectedFile?.error
                    ? 'border-red-300 bg-red-50'
                    : 'border-blue-300 hover:border-blue-400 bg-blue-50/50 hover:bg-blue-50'
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
                  <div className="space-y-4">
                    <FileText className="mx-auto h-16 w-16 text-blue-500" />
                    <div>
                      <p className="text-lg font-medium text-gray-900">
                        {selectedFile.file.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    {selectedFile.error && (
                      <p className="text-sm text-red-600">
                        {selectedFile.error}
                      </p>
                    )}
                    <Button
                      variant="outline"
                      onClick={() => setSelectedFile(null)}
                    >
                      Remove File
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Upload className="mx-auto h-16 w-16 text-blue-400" />
                    <div>
                      <label
                        htmlFor="file-upload"
                        className="cursor-pointer text-lg font-medium text-blue-600 hover:text-blue-500"
                      >
                        Click to upload
                      </label>
                      <span className="text-gray-500"> or drag and drop</span>
                    </div>
                    <p className="text-sm text-gray-500">
                      PDF, JPG, PNG up to 10MB
                    </p>
                  </div>
                )}
              </div>

              {/* Contract Name Input */}
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Contract Name
                </label>
                <Input
                  type="text"
                  placeholder="e.g., Apartment Lease Agreement 2024"
                  value={contractName}
                  onChange={(e) => setContractName(e.target.value)}
                  className="w-full text-lg"
                />
              </div>

              {/* Upload Error */}
              {uploadError && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">{uploadError}</p>
                </div>
              )}

              {/* Start Button */}
              <Button
                onClick={startWorkflow}
                disabled={!selectedFile?.file || !contractName.trim() || isUploading || !!selectedFile?.error}
                className="w-full mt-6 h-12 text-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                size="lg"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
                    Starting Workflow...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-5 w-5" />
                    Start Interactive Processing
                  </>
                )}
              </Button>
            </Card>
          </div>
        ) : (
          /* Interactive Agentic Flow */
          <div className="space-y-6">
            {/* Workflow Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Button
                  variant="outline"
                  onClick={resetWorkflow}
                  className="flex items-center"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  New Workflow
                </Button>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Processing: {contractName}
                  </h2>
                  {currentWorkflow && (
                    <p className="text-sm text-gray-600">
                      Workflow ID: {currentWorkflow.workflow_id}
                    </p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Badge variant={wsConnected ? 'success' : 'secondary'}>
                  {wsConnected ? '🔗 Connected' : '⚠️ Disconnected'}
                </Badge>
                <Badge variant="primary">
                  Interactive Mode
                </Badge>
              </div>
            </div>

            {/* Interactive Flow Component */}
            <InteractiveAgenticFlow
              workflowId={currentWorkflow?.workflow_id}
              contractName={contractName}
              onStepComplete={handleStepComplete}
              onWorkflowComplete={handleWorkflowComplete}
              workflowEvents={workflowEvents}
              realTimeMode={wsConnected}
              humanInputData={humanInputData}
              showHumanInputPopup={showHumanInputPopup}
              onHumanInputSubmitted={() => {
                setShowHumanInputPopup(false);
                setHumanInputData(null);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default InteractiveWorkflow;