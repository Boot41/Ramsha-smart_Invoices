import React, { useState } from 'react';
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
      const userId = user?.id || 'user123';
      
      const result = await contractsApi.startInvoiceWorkflow(selectedFile, userId, selectedFile.name);
      
      setWorkflowId(result.workflow_id);

      setUploadSuccess(`Workflow for "${selectedFile.name}" started successfully!`);
      
      setSelectedFile(null);
      
      setTimeout(() => {
        setShowUploadDialog(false);
        setUploadSuccess(null);
        navigate(`/workflow/${result.workflow_id}`);
      }, 2000);
      
    } catch (error) {
      console.error('Contract upload failed:', error);
      setUploadError(error instanceof Error ? error.message : 'Failed to process contract. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSelectContract = (agreement: RentalAgreement) => {
    // This function is not used in the current workflow
    // but we can keep it for future use.
    console.log('Selected contract:', agreement);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Rental Agreements</h1>
          <p className="text-slate-600 mt-2">Manage your property rental contracts and agreements</p>
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
          <CardTitle>Rental Agreements ({filteredAgreements.length})</CardTitle>
          <CardDescription>
            {isLoading ? 'Loading contracts...' : 'Click on an agreement to generate invoices and manage scheduling'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Property</TableHead>
                <TableHead>Tenant</TableHead>
                <TableHead>Monthly Rent</TableHead>
                <TableHead>Lease Period</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
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
                      <div className="font-medium text-slate-900">{agreement.propertyTitle || agreement.contract_title}</div>
                      <div className="text-sm text-slate-500">{agreement.propertyAddress || agreement.address}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium text-slate-900">{agreement.tenantName || agreement.client?.name}</div>
                      <div className="text-sm text-slate-500">{agreement.tenantEmail || agreement.client?.email}</div>
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
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm">View</Button>
                      <Button variant="outline" size="sm">Edit</Button>
                    </div>
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
    </div>
  );
};

export default ContractsList;