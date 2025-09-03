import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '../../components/ui/Table';
import { contractsApi } from '../../../api/contracts';
import type { SelectOption } from '@types/index';
import { useContractStore } from '../../../stores/contractStore';
import { useAuth } from '../../../hooks/useAuth';

import { useInvoiceStore } from '../../../stores/invoiceStore';
import WorkflowPopupPro from '../../components/workflow/WorkflowPopupPro';
import { workflowAPI } from '../../services/workflowService';

// Debug log to verify import works
console.log('ContractsApi loaded:', !!contractsApi);

const ContractsList: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { setWorkflowId } = useInvoiceStore();
  const {
    contracts,
    fetchContracts,
    isLoading
  } = useContractStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Workflow popup state
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [contractName, setContractName] = useState<string>('');
  const [showWorkflowPopup, setShowWorkflowPopup] = useState(false);
  const [workflowMessages, setWorkflowMessages] = useState<any[]>([]);
  const [workflowSocket, setWorkflowSocket] = useState<WebSocket | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<any>(null);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [humanInputRequired, setHumanInputRequired] = useState<any | null>(null);

  // Enhanced WebSocket connection for workflow updates
  useEffect(() => {
    if (currentWorkflowId) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = process.env.NODE_ENV === 'development' ? 'localhost:8000' : window.location.host;
      const wsUrl = `${protocol}//${host}/api/v1/orchestrator/ws/workflow/${currentWorkflowId}/realtime`;
      
      console.log('🔗 Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Workflow WebSocket connected');
        setWorkflowSocket(ws);
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        setWorkflowMessages(prev => [...prev, { ...message, timestamp: new Date().toISOString() }]);

        // Enhanced message handling for better validation pausing
        console.log('📨 WebSocket message received:', message.type, message.data);
        
        switch (message.type) {
          case 'human_input_required':
          case 'human_input_needed':
            console.log('🚨 Human input required - setting up form...', message.data);
            setHumanInputRequired(message.data);
            setIsPaused(true);
            setWorkflowStatus((prev: any) => ({ ...(prev || {}), processing_status: 'needs_human_input' }));
            break;
          
          case 'status_update':
          case 'agent_transition':
          case 'agent_started':
            console.log('🔄 Status update:', message.data);
            setWorkflowStatus(message.data);
            break;
          
          case 'workflow_complete':
          case 'workflow_completed':
            console.log('✅ Workflow completed');
            setWorkflowStatus({ ...message.data, status: 'completed' });
            setIsPaused(false);
            break;
          
          case 'workflow_error':
          case 'error':
            console.log('❌ Workflow error:', message.data);
            setWorkflowStatus({ ...message.data, status: 'error' });
            setIsPaused(false);
            break;
          
          case 'input_processed':
          case 'human_input_processed':
            console.log('✅ Human input processed - resuming workflow');
            setHumanInputRequired(null);
            setIsPaused(false);
            break;
        }
      };

      ws.onclose = () => {
        console.log('Workflow WebSocket disconnected');
        setWorkflowSocket(null);
      };

      ws.onerror = (error) => {
        console.error('Workflow WebSocket error:', error);
      };

      return () => {
        ws.close();
      };
    }
  }, [currentWorkflowId]);

  // Cleanup WebSocket on component unmount
  useEffect(() => {
    return () => {
      if (workflowSocket) {
        workflowSocket.close();
      }
    };
  }, [workflowSocket]);

  React.useEffect(() => {
    let userId = user?.id;
    if (userId) {
      localStorage.setItem('userId', userId);
    } else {
      userId = localStorage.getItem('userId') || '';
    }
    if (userId) {
      console.log('Calling fetchContracts with userId:', userId);
      fetchContracts(userId);
    } else {
      console.error('No userId available for fetchContracts');
    }
  }, [user?.id, fetchContracts]);

  const statusOptions: SelectOption[] = [
    { value: '', label: 'All Statuses' },
    { value: 'active', label: 'Active' },
    { value: 'pending_signature', label: 'Pending Signature' },
    { value: 'expired', label: 'Expired' },
    { value: 'terminated', label: 'Terminated' }
  ];

  const propertyTypeOptions: SelectOption[] = [
    { value: '', label: 'All Property Types' },
    { value: 'apartment', label: 'Apartment' },
    { value: 'house', label: 'House' },
    { value: 'condo', label: 'Condo' },
    { value: 'townhouse', label: 'Townhouse' }
  ];

  const filteredAgreements = contracts.filter((agreement: any) => {
    const matchesSearch = (agreement.propertyTitle?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (agreement.tenantName?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (agreement.propertyAddress?.toLowerCase() || '').includes(searchTerm.toLowerCase());
    const matchesStatus = !statusFilter || agreement.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'pending_signature': return 'warning';
      case 'expired': return 'error';
      case 'terminated': return 'secondary';
      default: return 'secondary';
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;
    
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    
    try {
      const userId = user?.id || localStorage.getItem('userId') || 'user123';
      
      const result = await contractsApi.startInvoiceWorkflow(selectedFile, userId, selectedFile.name);
      
      setWorkflowId(result.workflow_id);
      setCurrentWorkflowId(result.workflow_id);
      setContractName(selectedFile.name);

      setUploadSuccess(`Workflow for "${selectedFile.name}" started successfully!`);
      
      // Reset form state
      setSelectedFile(null);
      setWorkflowMessages([]);
      setWorkflowStatus(null);
      setHumanInputRequired(null);
      
      // Show workflow popup after a brief success message
      setTimeout(() => {
        setShowUploadDialog(false);
        setUploadSuccess(null);
        setShowWorkflowPopup(true);
      }, 1000);
      
    } catch (error) {
      console.error('Contract upload failed:', error);
      setUploadError(error instanceof Error ? error.message : 'Failed to process contract. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // Enhanced workflow popup handlers
  const handleHumanInputSubmit = async (fieldValues: Record<string, any>, userNotes: string) => {
    console.log('📝 Submitting human input:', fieldValues, userNotes);
    
    try {
      // Try WebSocket first (real-time)
      if (workflowSocket && workflowSocket.readyState === WebSocket.OPEN) {
        const message = {
          type: 'human_input_submission',
          data: {
            field_values: fieldValues,
            user_notes: userNotes,
            workflow_id: currentWorkflowId,
            action: 'resume_workflow'
          }
        };
        workflowSocket.send(JSON.stringify(message));
        console.log('✅ Human input submitted via WebSocket', message);
        
  // Immediately update UI to show processing resuming
  setHumanInputRequired(null);
  setIsPaused(false);
  setWorkflowStatus((prev: any) => ({ ...(prev || {}), processing_status: 'processing' }));
        
      } else {
        // Fallback to HTTP API if WebSocket is not available
        console.log('🔄 WebSocket not available, using HTTP API fallback...');
        if (currentWorkflowId) {
          await workflowAPI.submitHumanInput(currentWorkflowId, fieldValues, userNotes);
          console.log('✅ Human input submitted via HTTP API');
          
          // Update UI state
          setHumanInputRequired(null);
          setIsPaused(false);
          setWorkflowStatus((prev: any) => ({ ...(prev || {}), processing_status: 'processing' }));
        }
      }
      
    } catch (error) {
      console.error('❌ Failed to submit human input:', error);
      alert('Failed to submit input. Please try again.');
    }
  };

  const handleHumanInputCancel = () => {
    setHumanInputRequired(null);
    // Optionally send a cancellation message to the workflow
    if (workflowSocket && workflowSocket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'human_input_cancelled',
        data: {
          message: 'User cancelled human input'
        }
      };
      workflowSocket.send(JSON.stringify(message));
    }
  };

  const handleWorkflowPopupClose = () => {
    setShowWorkflowPopup(false);
  };

  const handleDownloadData = async () => {
    try {
      if (currentWorkflowId) {
        const data = await workflowAPI.getWorkflowInvoiceData(currentWorkflowId);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `invoice-data-${currentWorkflowId}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to download invoice data:', error);
    }
  };

  const handleViewTemplates = () => {
    // Navigate to templates page - adjust based on your routing
    navigate('/invoices/templates');
  };

  const handleSelectContract = (agreement: any) => {
    // This function is not used in the current workflow
    // but we can keep it for future use.
    console.log('Selected contract:', agreement);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Service Agreements</h1>
          <p className="text-slate-600 mt-2">Manage your service contracts and agreements</p>
        </div>
        <Button 
          onClick={() => setShowUploadDialog(true)} 
          variant="primary"
          className="flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Upload Agreement
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Total Agreements</p>
                <p className="text-2xl font-bold text-slate-900">{contracts.length}</p>
              </div>
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Active</p>
                <p className="text-2xl font-bold text-green-600">
                  {contracts.filter((a: any) => a.status === 'active').length}
                </p>
              </div>
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Pending</p>
                <p className="text-2xl font-bold text-amber-600">
                  {contracts.filter((a: any) => a.status === 'pending_signature').length}
                </p>
              </div>
              <div className="p-2 bg-amber-100 rounded-lg">
                <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Monthly Revenue</p>
                <p className="text-2xl font-bold text-slate-900">
                  ${contracts.reduce((sum: number, a: any) => sum + (a.monthlyRent || 0), 0).toLocaleString()}
                </p>
              </div>
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Agreements</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              placeholder="Search by property, tenant, or address..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Select
              options={statusOptions}
              placeholder="Filter by status"
              value={statusFilter}
              onChange={setStatusFilter}
            />
            <Select
              options={propertyTypeOptions}
              placeholder="Filter by property type"
              value=""
              onChange={() => {}}
            />
          </div>
        </CardContent>
      </Card>

      {/* Agreements Table */}
      <Card>
        <CardHeader>
          <CardTitle>Service Agreements ({filteredAgreements.length})</CardTitle>
          <CardDescription>
            {isLoading ? 'Loading contracts...' : 'Manage your service agreements and contracts'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Contract</TableHead>
                <TableHead>Client</TableHead>
                <TableHead>Monthly Fee</TableHead>
                <TableHead>Service Period</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAgreements.map((agreement: any) => (
                <TableRow 
                  key={agreement.id || agreement.contract_id} 
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => handleSelectContract(agreement)}
                >
                  <TableCell>
                    <div>
                      <div className="font-medium text-slate-900">{agreement.contract_number || agreement.contract_title || agreement.propertyTitle || 'Contract'}</div>
                      <div className="text-sm text-slate-500">{agreement.service_type || agreement.propertyAddress || agreement.address || 'Service Agreement'}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium text-slate-900">{agreement.client_name || agreement.tenantName || agreement.client?.name || 'Client'}</div>
                      <div className="text-sm text-slate-500">{agreement.client_email || agreement.tenantEmail || agreement.client?.email || 'No email'}</div>
                    </div>
                  </TableCell>
                  <TableCell className="font-semibold text-slate-900">
                    ${agreement.monthlyRent ? agreement.monthlyRent.toLocaleString() : (agreement.payment_terms?.amount || 0).toLocaleString()}/month
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      <div>{agreement.leaseStartDate ? new Date(agreement.leaseStartDate).toLocaleDateString() : (agreement.start_date ? new Date(agreement.start_date).toLocaleDateString() : '')}</div>
                      <div className="text-slate-500">to {agreement.leaseEndDate ? new Date(agreement.leaseEndDate).toLocaleDateString() : (agreement.end_date ? new Date(agreement.end_date).toLocaleDateString() : '')}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(agreement.status)}>
                      {agreement.status ? agreement.status.replace('_', ' ') : 'Unknown'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      {showUploadDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle>Upload Rental Agreement</CardTitle>
              <CardDescription>
                Upload a new rental agreement document (PDF only)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {uploadError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-700">{uploadError}</p>
                </div>
              )}
              
              {uploadSuccess && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                  <p className="text-sm text-green-700">{uploadSuccess}</p>
                </div>
              )}
              
              <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="flex flex-col items-center">
                    <svg className="w-12 h-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="text-sm text-slate-600 mb-2">
                      {selectedFile ? selectedFile.name : 'Click to select a file or drag and drop'}
                    </p>
                    <p className="text-xs text-slate-400">
                      PDF up to 10MB
                    </p>
                  </div>
                </label>
              </div>
            </CardContent>
            <CardFooter className="flex space-x-3">
              <Button variant="outline" onClick={() => setShowUploadDialog(false)}>
                Cancel
              </Button>
              <Button 
                variant="primary" 
                onClick={handleUploadSubmit}
                disabled={!selectedFile || isUploading}
              >
                {isUploading ? 'Processing...' : 'Upload Agreement'}
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* Enhanced Workflow Popup */}
      {currentWorkflowId && (
        <WorkflowPopupPro
          workflowId={currentWorkflowId}
          contractName={contractName}
          isOpen={showWorkflowPopup}
          onClose={handleWorkflowPopupClose}
          workflowStatus={workflowStatus}
          events={workflowMessages}
          humanInputRequest={humanInputRequired}
          onSubmitHumanInput={handleHumanInputSubmit}
          onCancelHumanInput={handleHumanInputCancel}
          onDownloadData={handleDownloadData}
          onViewTemplates={handleViewTemplates}
        />
      )}
    </div>
  );
};

export default ContractsList;