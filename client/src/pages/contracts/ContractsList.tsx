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
import { workflowAPI } from '../../services/workflowService';

// Debug log to verify import works
console.log('ContractsApi loaded:', !!contractsApi);

const ContractsList: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { setWorkflowId } = useInvoiceStore();
  const {
    contracts,
    mcpContracts,
    allContracts,
    fetchContracts,
    syncMCPContracts,
    startAgenticWorkflow,
    isLoading,
    isSyncingMCP,
    error,
    mcpError,
    lastMCPSync,
    clearError,
    clearMCPError
  } = useContractStore();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isRefreshingAuth, setIsRefreshingAuth] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Workflow state - simplified for redirect approach
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [contractName, setContractName] = useState<string>('');
  const [loadingContracts, setLoadingContracts] = useState<Set<string>>(new Set());

  // Removed polling logic - workflows now redirect to dedicated status page


  // Load contracts on component mount
  React.useEffect(() => {
    let userId = user?.id;
    if (userId) {
      localStorage.setItem('userId', userId);
    } else {
      userId = localStorage.getItem('userId') || '';
    }
    if (userId) {
      console.log('Loading contracts for user:', userId);
      Promise.all([
        fetchContracts(userId).catch(console.error),
        syncMCPContracts(userId).catch(console.error)
      ]);
    } else {
      console.error('No userId available for fetchContracts');
    }
  }, [user?.id, fetchContracts, syncMCPContracts]);

  const statusOptions: SelectOption[] = [
    { value: '', label: 'All Statuses' },
    { value: 'active', label: 'Active' },
    { value: 'pending_signature', label: 'Pending Signature' },
    { value: 'expired', label: 'Expired' },
    { value: 'terminated', label: 'Terminated' },
    { value: 'processed', label: 'Processed' },
    { value: 'failed', label: 'Failed' }
  ];

  const sourceOptions: SelectOption[] = [
    { value: '', label: 'All Sources' },
    { value: 'manual', label: '📄 Manual Upload' },
    { value: 'mcp', label: '☁️ Google Drive (MCP)' }
  ];

  const filteredContracts = allContracts.filter((contract: any) => {
    const searchFields = [
      contract.propertyTitle,
      contract.tenantName, 
      contract.propertyAddress,
      contract.name,
      contract.contract_name,
      contract.client_name,
      contract.service_type,
      contract.contract_title
    ].filter(Boolean);
    
    const matchesSearch = !searchTerm || 
      searchFields.some(field => 
        field?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    
    const matchesStatus = !statusFilter || contract.status === statusFilter || 
      (contract.processed && statusFilter === 'processed') ||
      (contract.processing_error && statusFilter === 'failed');
      
    const matchesSource = !sourceFilter || contract.source === sourceFilter;
    
    return matchesSearch && matchesStatus && matchesSource;
  });

  const getStatusBadgeVariant = (contract: any) => {
    if (contract.source === 'mcp') {
      if (contract.processed) return 'success';
      if (contract.processing_error) return 'error';
      return 'warning';
    }
    
    switch (contract.status) {
      case 'active': return 'success';
      case 'pending_signature': return 'warning';
      case 'expired': return 'error';
      case 'terminated': return 'secondary';
      default: return 'secondary';
    }
  };

  const getStatusText = (contract: any) => {
    if (contract.source === 'mcp') {
      if (contract.processed) return 'Processed';
      if (contract.processing_error) return 'Failed';
      return 'Synced';
    }
    return contract.status ? contract.status.replace('_', ' ') : 'Unknown';
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
      
      // Navigate to workflow status page after a brief success message
      setTimeout(() => {
        setShowUploadDialog(false);
        setUploadSuccess(null);
        navigate(`/workflow/${result.workflow_id}`, {
          state: { 
            contractName,
            workflowId: result.workflow_id,
            fromUpload: true 
          }
        });
      }, 1000);
      
    } catch (error) {
      console.error('Contract upload failed:', error);
      setUploadError(error instanceof Error ? error.message : 'Failed to process contract. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSyncGoogleDrive = async () => {
    const userId = user?.id || localStorage.getItem('userId') || '';
    if (!userId) {
      console.error('No user ID available for sync');
      return;
    }
    
    try {
      await syncMCPContracts(userId, 'contract OR agreement', true);
    } catch (error) {
      console.error('Sync failed:', error);
    }
  };

  const handleRefreshAuth = async () => {
    setIsRefreshingAuth(true);
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch('/auth/google-drive', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        setUploadSuccess(data.message);
        // Clear success message after 5 seconds
        setTimeout(() => setUploadSuccess(null), 5000);
      } else {
        setUploadError(data.message || 'Failed to refresh Google Drive authentication');
        // Clear error message after 5 seconds
        setTimeout(() => setUploadError(null), 5000);
      }
    } catch (error: any) {
      console.error('Failed to refresh Google Drive auth:', error);
      setUploadError('Failed to refresh Google Drive authentication');
      setTimeout(() => setUploadError(null), 5000);
    } finally {
      setIsRefreshingAuth(false);
    }
  };

  // Removed workflow popup handlers - now using dedicated workflow status page

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

  const handleSelectContract = (contract: any) => {
    console.log('Selected contract:', contract);
    // You can implement contract selection logic here
  };

  const handleStartAgenticWorkflow = async (contract: any) => {
    const userId = user?.id || localStorage.getItem('userId') || '';
    if (!userId) {
      console.error('No user ID available for starting agentic workflow');
      return;
    }

    const contractId = contract.id || contract.file_id || contract.contract_id || contract.name;
    
    // Add this contract to loading state
    setLoadingContracts(prev => new Set(prev).add(contractId));

    try {
      console.log('Starting agentic workflow for contract:', contract);
      
      const contractName = contract.name || 
                        contract.contract_name || 
                        contract.contract_title || 
                        contract.propertyTitle || 
                        contract.title || 
                        contract.filename || 
                        contract.file_name ||
                        contract.document_name ||
                        contract.id ||
                        'Untitled Contract';
      const contractPath = contract.file_path || 
                          contract.path || 
                          contract.gdrive_uri || 
                          contract.url || 
                          contract.file_id ||
                          contract.document_id ||
                          contractName;
      
      console.log('🔍 Debug contract data:', {
        contract,
        contractName,
        contractPath,
        file_path: contract.file_path,
        path: contract.path,
        gdrive_uri: contract.gdrive_uri
      });
      
      const result = await startAgenticWorkflow(userId, contractName, contractPath);
      
      // Set workflow state for UI
      setWorkflowId(result.workflow_id);
      setCurrentWorkflowId(result.workflow_id);
      setContractName(contractName);
      
      // Reset workflow UI state
      
      // Navigate to workflow status page
      navigate(`/workflow/${result.workflow_id}`, {
        state: { 
          contractName: contractName,
          workflowId: result.workflow_id,
          fromContract: true 
        }
      });
      
      console.log('Agentic workflow started successfully:', result);
    } catch (error) {
      console.error('Failed to start agentic workflow:', error);
    } finally {
      // Remove this contract from loading state
      setLoadingContracts(prev => {
        const newSet = new Set(prev);
        newSet.delete(contractId);
        return newSet;
      });
    }
  };

  const getContractIcon = (contract: any) => {
    if (contract.source === 'mcp') {
      return (
        <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
          <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>
      );
    }
    return (
      <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Smart Contract Manager</h1>
          <p className="text-slate-600 mt-2">
            Manage contracts from manual uploads and Google Drive sync
          </p>
        </div>
        <div className="flex gap-3">
          <Button 
            onClick={handleSyncGoogleDrive} 
            variant="outline"
            className="flex items-center gap-2"
            disabled={isSyncingMCP}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
            {isSyncingMCP ? 'Syncing...' : 'Sync Google Drive'}
          </Button>
          <Button 
            onClick={() => setShowUploadDialog(true)} 
            variant="primary"
            className="flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Upload Contract
          </Button>
          <Button 
            onClick={handleRefreshAuth} 
            variant="outline"
            className="flex items-center gap-2"
            disabled={isRefreshingAuth}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12.017 3L4.5 13.5h15.036L12.017 3z"/>
              <path d="M6.017 15L9.517 21H14.517L11.017 15H6.017z"/>
              <path d="M7.018 9.5L10.518 3.5H19.518L16.018 9.5H7.018z"/>
            </svg>
            {isRefreshingAuth ? 'Refreshing...' : 'Re-authenticate Google Drive'}
          </Button>
        </div>
      </div>

      {/* Error Messages */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex justify-between items-center">
          <p className="text-red-700">{error}</p>
          <Button variant="outline" size="sm" onClick={clearError}>Dismiss</Button>
        </div>
      )}
      
      {mcpError && (
        <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg flex justify-between items-center">
          <p className="text-orange-700">{mcpError}</p>
          <Button variant="outline" size="sm" onClick={clearMCPError}>Dismiss</Button>
        </div>
      )}

      {/* Success Message */}
      {lastMCPSync && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-700 font-medium">✅ Google Drive Sync Complete</p>
          <p className="text-green-600 text-sm mt-1">
            Found {lastMCPSync.total_count} files, processed {lastMCPSync.processed_count} contracts
          </p>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Total Contracts</p>
                <p className="text-2xl font-bold text-slate-900">{allContracts.length}</p>
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
                <p className="text-sm font-medium text-slate-600">Manual Uploads</p>
                <p className="text-2xl font-bold text-blue-600">{contracts.length}</p>
              </div>
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Google Drive (MCP)</p>
                <p className="text-2xl font-bold text-green-600">{mcpContracts.length}</p>
              </div>
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Processed Successfully</p>
                <p className="text-2xl font-bold text-purple-600">
                  {allContracts.filter(c => c.processed || c.status === 'active').length}
                </p>
              </div>
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filter & Search Contracts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              placeholder="Search contracts, clients, services..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Select
              options={sourceOptions}
              placeholder="Filter by source"
              value={sourceFilter}
              onChange={setSourceFilter}
            />
            <Select
              options={statusOptions}
              placeholder="Filter by status"
              value={statusFilter}
              onChange={setStatusFilter}
            />
          </div>
        </CardContent>
      </Card>

      {/* Contracts Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Contracts ({filteredContracts.length})</CardTitle>
          <CardDescription>
            {isLoading || isSyncingMCP ? 'Loading contracts...' : 'Manage your contracts from all sources'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredContracts.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto bg-slate-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">No contracts found</h3>
              <p className="text-slate-600 mb-4">
                Upload a contract manually or sync from Google Drive to get started.
              </p>
              <div className="flex justify-center gap-3 flex-wrap">
                <Button onClick={() => setShowUploadDialog(true)} variant="primary">
                  Upload Contract
                </Button>
                <Button onClick={handleSyncGoogleDrive} variant="outline" disabled={isSyncingMCP}>
                  {isSyncingMCP ? 'Syncing...' : 'Sync Google Drive'}
                </Button>
                <Button 
                  onClick={handleRefreshAuth} 
                  variant="outline"
                  className="flex items-center gap-2"
                  disabled={isRefreshingAuth}
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12.017 3L4.5 13.5h15.036L12.017 3z"/>
                    <path d="M6.017 15L9.517 21H14.517L11.017 15H6.017z"/>
                    <path d="M7.018 9.5L10.518 3.5H19.518L16.018 9.5H7.018z"/>
                  </svg>
                  {isRefreshingAuth ? 'Refreshing...' : 'Re-authenticate'}
                </Button>
              </div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Contract</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Client/Service</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredContracts.map((contract: any, index) => (
                  <TableRow 
                    key={contract.id || contract.file_id || contract.contract_id || index} 
                    className="cursor-pointer hover:bg-slate-50"
                    onClick={() => handleSelectContract(contract)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {getContractIcon(contract)}
                        <div>
                          <div className="font-medium text-slate-900">
                            {contract.name || contract.contract_name || contract.contract_title || contract.propertyTitle || 'Contract'}
                          </div>
                          <div className="text-sm text-slate-500">
                            {contract.mime_type || contract.service_type || contract.propertyAddress || 'Contract Document'}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge 
                        variant={contract.source === 'mcp' ? 'success' : 'secondary'}
                        className="text-xs"
                      >
                        {contract.source === 'mcp' ? '☁️ Google Drive' : '📄 Manual Upload'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium text-slate-900">
                          {contract.client_name || contract.tenantName || contract.client?.name || 'Client'}
                        </div>
                        <div className="text-sm text-slate-500">
                          {contract.client_email || contract.tenantEmail || contract.client?.email || 'No email'}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {contract.monthlyRent && (
                          <div className="font-semibold text-slate-900">
                            ${contract.monthlyRent.toLocaleString()}/month
                          </div>
                        )}
                        {contract.payment_terms?.amount && (
                          <div className="font-semibold text-slate-900">
                            ${contract.payment_terms.amount.toLocaleString()}
                          </div>
                        )}
                        <div className="text-slate-500">
                          {contract.leaseStartDate && new Date(contract.leaseStartDate).toLocaleDateString()}
                          {contract.start_date && new Date(contract.start_date).toLocaleDateString()}
                          {(contract.leaseStartDate || contract.start_date) && ' - '}
                          {contract.leaseEndDate && new Date(contract.leaseEndDate).toLocaleDateString()}
                          {contract.end_date && new Date(contract.end_date).toLocaleDateString()}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(contract)}>
                        {getStatusText(contract)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="primary"
                        size="sm"
                        className="px-6 py-3 text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartAgenticWorkflow(contract);
                        }}
                        disabled={loadingContracts.has(contract.id || contract.file_id || contract.contract_id || contract.name)}
                      >
                        {loadingContracts.has(contract.id || contract.file_id || contract.contract_id || contract.name) ? 'Starting...' : 'Generate Invoice'}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      {showUploadDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle>Upload Contract</CardTitle>
              <CardDescription>
                Upload a new contract document to start the AI processing workflow
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
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="flex flex-col items-center">
                    <svg className="w-12 h-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-sm text-slate-600 mb-2">
                      {selectedFile ? selectedFile.name : 'Click to select a file or drag and drop'}
                    </p>
                    <p className="text-xs text-slate-400">
                      PDF, DOC, or DOCX up to 10MB
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
                {isUploading ? 'Processing...' : 'Start AI Workflow'}
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* Workflow popup removed - workflows now redirect to dedicated status page */}
    </div>
  );
};

export default ContractsList;