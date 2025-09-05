import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ProfessionalInvoiceTemplate from '../../components/invoices/ProfessionalInvoiceTemplate';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { invoicesAPI } from '../../../api/invoices';
import { useAuth } from '../../../hooks/useAuth';

const InvoicesPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'template'>('list');

  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: 'draft', label: 'Draft' },
    { value: 'generated', label: 'Generated' },
    { value: 'sent', label: 'Sent' },
    { value: 'paid', label: 'Paid' },
    { value: 'overdue', label: 'Overdue' },
    { value: 'cancelled', label: 'Cancelled' }
  ];

  useEffect(() => {
    loadInvoices();
  }, [currentPage, statusFilter]);

  const loadInvoices = async () => {
    if (!user?.id) {
      setError('User not authenticated');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response: InvoiceListResponse = await invoicesAPI.getInvoices(
        user.id,
        currentPage,
        10,
        statusFilter || undefined
      );
      
      setInvoices(response.invoices);
      setTotalPages(Math.ceil(response.total / response.per_page));
      setError(null);
    } catch (err) {
      console.error('Failed to load invoices:', err);
      setError('Failed to load invoices. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (invoiceId: string) => {
    try {
      const blob = await invoicesAPI.downloadInvoice(invoiceId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download invoice:', err);
      alert('Failed to download invoice. Please try again.');
    }
  };

  const handleSend = async (invoiceId: string) => {
    const invoice = invoices.find(inv => inv.id === invoiceId);
    if (!invoice) return;

    const email = prompt(`Send invoice to:`, invoice.client_email || '');
    if (!email) return;

    try {
      await invoicesAPI.sendInvoice(invoiceId, email);
      alert('Invoice sent successfully!');
      loadInvoices(); // Refresh to get updated status
    } catch (err) {
      console.error('Failed to send invoice:', err);
      alert('Failed to send invoice. Please try again.');
    }
  };

  const handleStatusChange = async (invoiceId: string, status: Invoice['status']) => {
    try {
      await invoicesAPI.updateInvoiceStatus(invoiceId, status);
      loadInvoices(); // Refresh the list
    } catch (err) {
      console.error('Failed to update invoice status:', err);
      alert('Failed to update invoice status. Please try again.');
    }
  };

  const getStatusColor = (status: Invoice['status']) => {
    const colors = {
      draft: 'secondary',
      generated: 'primary',
      sent: 'warning',
      paid: 'success',
      overdue: 'error',
      cancelled: 'secondary'
    } as const;
    return colors[status] || 'secondary';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const filteredInvoices = invoices.filter(invoice =>
    searchTerm === '' || 
    invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.client_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.service_provider_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading invoices...</p>
        </div>
      </div>
    );
  }

  if (selectedInvoice && viewMode === 'template') {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6 flex items-center gap-4">
            <Button
              variant="outline"
              onClick={() => {
                setSelectedInvoice(null);
                setViewMode('list');
              }}
              className="flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to List
            </Button>
            <h1 className="text-2xl font-bold text-gray-900">Invoice #{selectedInvoice.invoice_number}</h1>
          </div>
          
          <ProfessionalInvoiceTemplate
            invoice={selectedInvoice}
            showActions={true}
            onDownload={handleDownload}
            onSend={handleSend}
            onStatusChange={handleStatusChange}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Invoices</h1>
              <p className="text-gray-600 mt-2">
                Manage and view your generated invoices
              </p>
            </div>
            <Button
              onClick={() => navigate('/contracts')}
              variant="primary"
              className="flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Generate New Invoice
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Filter & Search</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                placeholder="Search invoices..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <Select
                options={statusOptions}
                placeholder="Filter by status"
                value={statusFilter}
                onChange={setStatusFilter}
              />
              <Button
                onClick={loadInvoices}
                variant="outline"
                className="flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Invoices List */}
        <Card>
          <CardHeader>
            <CardTitle>
              Invoices ({filteredInvoices.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredInvoices.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No invoices found</h3>
                <p className="text-gray-600 mb-4">
                  Start by generating invoices from your contracts.
                </p>
                <Button
                  onClick={() => navigate('/contracts')}
                  variant="primary"
                >
                  Generate Invoice
                </Button>
              </div>
            ) : (
              <div className="grid gap-4">
                {filteredInvoices.map((invoice) => (
                  <div
                    key={invoice.id}
                    className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => {
                      setSelectedInvoice(invoice);
                      setViewMode('template');
                    }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          #{invoice.invoice_number}
                        </h3>
                        <p className="text-gray-600 text-sm">
                          {invoice.client_name} • {formatDate(invoice.invoice_date)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant={getStatusColor(invoice.status)}>
                          {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                        </Badge>
                        <div className="text-right">
                          <p className="text-lg font-bold text-gray-900">
                            {formatCurrency(invoice.total_amount, invoice.currency)}
                          </p>
                          <p className="text-sm text-gray-500">
                            Due: {formatDate(invoice.due_date)}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Service Provider:</span>
                        <p className="font-medium text-gray-900">{invoice.service_provider_name}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Contract:</span>
                        <p className="font-medium text-gray-900">{invoice.contract_title || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Type:</span>
                        <p className="font-medium text-gray-900 capitalize">
                          {invoice.contract_type?.replace('_', ' ') || 'N/A'}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500">Generated:</span>
                        <p className="font-medium text-gray-900">{formatDate(invoice.created_at)}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload(invoice.id);
                        }}
                      >
                        Download
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSend(invoice.id);
                        }}
                      >
                        Send
                      </Button>
                      {invoice.confidence_score && (
                        <span className="text-xs text-gray-500">
                          Confidence: {(invoice.confidence_score * 100).toFixed(0)}%
                        </span>
                      )}
                      {invoice.human_reviewed && (
                        <Badge variant="success" className="text-xs">
                          Human Reviewed
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex justify-center gap-2">
            <Button
              variant="outline"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(currentPage - 1)}
            >
              Previous
            </Button>
            
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <Button
                key={page}
                variant={page === currentPage ? "primary" : "outline"}
                onClick={() => setCurrentPage(page)}
                className="w-10"
              >
                {page}
              </Button>
            ))}
            
            <Button
              variant="outline"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default InvoicesPage;