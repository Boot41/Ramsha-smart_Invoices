import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { FileText, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';

interface ExtractedInvoiceDataProps {
  invoiceData: any;
  workflowStatus?: any;
}

const ExtractedInvoiceData: React.FC<ExtractedInvoiceDataProps> = ({ 
  invoiceData, 
  workflowStatus 
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['summary']));
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  // Extract the original invoice data from the nested structure
  const originalData = invoiceData?.processing_metadata?.original_invoice_data || invoiceData;
  
  if (!originalData) {
    return null;
  }

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const copyToClipboard = async (data: any, sectionName: string) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopiedSection(sectionName);
      setTimeout(() => setCopiedSection(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const renderSection = (title: string, sectionKey: string, content: React.ReactNode, data?: any) => {
    const isExpanded = expandedSections.has(sectionKey);
    
    return (
      <div className="border border-gray-200 rounded-lg mb-4">
        <div 
          className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
          onClick={() => toggleSection(sectionKey)}
        >
          <div className="flex items-center space-x-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-500" />
            )}
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>
          {data && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                copyToClipboard(data, sectionKey);
              }}
              className="ml-2"
            >
              {copiedSection === sectionKey ? (
                <Check className="h-3 w-3" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          )}
        </div>
        {isExpanded && (
          <div className="p-4 border-t border-gray-200">
            {content}
          </div>
        )}
      </div>
    );
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <FileText className="h-5 w-5 text-blue-500" />
          <h2 className="text-xl font-bold text-gray-900">📄 Extracted Invoice Data</h2>
        </div>
        <div className="flex space-x-2">
          {originalData.metadata?.confidence_score && (
            <Badge variant={originalData.metadata.confidence_score > 0.7 ? 'success' : 'warning'}>
              {(originalData.metadata.confidence_score * 100).toFixed(0)}% Confidence
            </Badge>
          )}
          {originalData.metadata?.quality_score && (
            <Badge variant="primary">
              Quality: {(originalData.metadata.quality_score * 100).toFixed(0)}%
            </Badge>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {/* Invoice Summary */}
        {renderSection(
          '📊 Invoice Summary',
          'summary',
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium text-gray-600">Invoice ID:</span>
                <p className="text-sm text-gray-900 font-mono bg-gray-100 px-2 py-1 rounded">
                  {originalData.invoice_header?.invoice_id || 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Contract Type:</span>
                <p className="text-sm text-gray-900 capitalize">
                  {originalData.contract_details?.contract_type?.replace('_', ' ') || 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Amount:</span>
                <p className="text-lg font-bold text-green-600">
                  {formatCurrency(originalData.totals?.total_amount || 0, originalData.payment_information?.currency)}
                </p>
              </div>
            </div>
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium text-gray-600">Invoice Date:</span>
                <p className="text-sm text-gray-900">
                  {formatDate(originalData.invoice_header?.invoice_date)}
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Due Date:</span>
                <p className="text-sm text-gray-900">
                  {formatDate(originalData.invoice_header?.due_date)}
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Payment Frequency:</span>
                <p className="text-sm text-gray-900 capitalize">
                  {originalData.payment_information?.frequency || 'N/A'}
                </p>
              </div>
            </div>
          </div>,
          originalData
        )}

        {/* Parties Information */}
        {originalData.parties && renderSection(
          '👥 Parties Information',
          'parties',
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2">Client</h4>
              <div className="space-y-1 text-sm">
                <p><span className="font-medium">Name:</span> {originalData.parties.client?.name || 'N/A'}</p>
                {originalData.parties.client?.email && (
                  <p><span className="font-medium">Email:</span> {originalData.parties.client.email}</p>
                )}
                {originalData.parties.client?.address && (
                  <p><span className="font-medium">Address:</span> {originalData.parties.client.address}</p>
                )}
                {originalData.parties.client?.phone && (
                  <p><span className="font-medium">Phone:</span> {originalData.parties.client.phone}</p>
                )}
              </div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <h4 className="font-semibold text-green-900 mb-2">Service Provider</h4>
              <div className="space-y-1 text-sm">
                <p><span className="font-medium">Name:</span> {originalData.parties.service_provider?.name || 'N/A'}</p>
                {originalData.parties.service_provider?.email && (
                  <p><span className="font-medium">Email:</span> {originalData.parties.service_provider.email}</p>
                )}
                {originalData.parties.service_provider?.address && (
                  <p><span className="font-medium">Address:</span> {originalData.parties.service_provider.address}</p>
                )}
                {originalData.parties.service_provider?.phone && (
                  <p><span className="font-medium">Phone:</span> {originalData.parties.service_provider.phone}</p>
                )}
              </div>
            </div>
          </div>,
          originalData.parties
        )}

        {/* Services/Items */}
        {originalData.services_and_items && originalData.services_and_items.length > 0 && renderSection(
          '🛍️ Services & Items',
          'services',
          <div className="space-y-4">
            {originalData.services_and_items.map((item: any, index: number) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                      <span>Qty: {item.quantity} {item.unit}</span>
                      <span>Rate: {formatCurrency(item.unit_price, originalData.payment_information?.currency)}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg text-gray-900">
                      {formatCurrency(item.total_amount, originalData.payment_information?.currency)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>,
          originalData.services_and_items
        )}

        {/* Payment Information */}
        {originalData.payment_information && renderSection(
          '💰 Payment Information',
          'payment',
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium text-gray-600">Amount:</span>
                <p className="text-lg font-bold text-green-600">
                  {formatCurrency(originalData.payment_information.amount, originalData.payment_information.currency)}
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Currency:</span>
                <p className="text-sm text-gray-900">{originalData.payment_information.currency}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Frequency:</span>
                <p className="text-sm text-gray-900 capitalize">{originalData.payment_information.frequency}</p>
              </div>
            </div>
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium text-gray-600">Due Days:</span>
                <p className="text-sm text-gray-900">{originalData.payment_information.due_days} days</p>
              </div>
              {originalData.payment_information.payment_method && (
                <div>
                  <span className="text-sm font-medium text-gray-600">Payment Method:</span>
                  <p className="text-sm text-gray-900 capitalize">
                    {originalData.payment_information.payment_method.replace('_', ' ')}
                  </p>
                </div>
              )}
              {originalData.payment_information.late_fee && (
                <div>
                  <span className="text-sm font-medium text-gray-600">Late Fee:</span>
                  <p className="text-sm text-gray-900">
                    {formatCurrency(originalData.payment_information.late_fee, originalData.payment_information.currency)}
                  </p>
                </div>
              )}
            </div>
          </div>,
          originalData.payment_information
        )}

        {/* Contract Details */}
        {originalData.contract_details && renderSection(
          '📋 Contract Details',
          'contract',
          <div className="space-y-3">
            {originalData.contract_details.start_date && (
              <div>
                <span className="text-sm font-medium text-gray-600">Contract Period:</span>
                <p className="text-sm text-gray-900">
                  {formatDate(originalData.contract_details.start_date)} to {formatDate(originalData.contract_details.end_date)}
                </p>
              </div>
            )}
            {originalData.contract_details.contract_type && (
              <div>
                <span className="text-sm font-medium text-gray-600">Type:</span>
                <p className="text-sm text-gray-900 capitalize">
                  {originalData.contract_details.contract_type.replace('_', ' ')}
                </p>
              </div>
            )}
          </div>,
          originalData.contract_details
        )}

        {/* Additional Terms */}
        {originalData.additional_terms && renderSection(
          '📜 Additional Terms',
          'terms',
          <div className="space-y-3">
            {originalData.additional_terms.special_terms && (
              <div>
                <span className="text-sm font-medium text-gray-600">Special Terms:</span>
                <p className="text-sm text-gray-700 mt-1 p-3 bg-gray-50 rounded">
                  {originalData.additional_terms.special_terms}
                </p>
              </div>
            )}
            {originalData.additional_terms.notes && (
              <div>
                <span className="text-sm font-medium text-gray-600">Notes:</span>
                <p className="text-sm text-gray-700 mt-1 p-3 bg-blue-50 rounded">
                  {originalData.additional_terms.notes}
                </p>
              </div>
            )}
          </div>,
          originalData.additional_terms
        )}

        {/* Processing Metadata */}
        {originalData.metadata && renderSection(
          '🔍 Processing Details',
          'metadata',
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div>
                <span className="font-medium text-gray-600">Generated By:</span>
                <p className="text-gray-900">{originalData.metadata.generated_by}</p>
              </div>
              <div>
                <span className="font-medium text-gray-600">Agent Version:</span>
                <p className="text-gray-900">{originalData.metadata.agent_version}</p>
              </div>
              <div>
                <span className="font-medium text-gray-600">Processing Time:</span>
                <p className="text-gray-900">{originalData.metadata.processing_time_seconds?.toFixed(2)}s</p>
              </div>
            </div>
            <div className="space-y-2">
              <div>
                <span className="font-medium text-gray-600">Human Input:</span>
                <Badge variant={originalData.metadata.human_input_applied ? 'success' : 'secondary'}>
                  {originalData.metadata.human_input_applied ? 'Applied' : 'Not Applied'}
                </Badge>
              </div>
              <div>
                <span className="font-medium text-gray-600">Validation:</span>
                <Badge variant={originalData.metadata.validation_passed ? 'success' : 'warning'}>
                  {originalData.metadata.validation_passed ? 'Passed' : 'Failed'}
                </Badge>
              </div>
              <div>
                <span className="font-medium text-gray-600">Validation Score:</span>
                <p className="text-gray-900">{(originalData.metadata.validation_score * 100).toFixed(0)}%</p>
              </div>
            </div>
          </div>,
          originalData.metadata
        )}

        {/* Raw JSON Data */}
        {renderSection(
          '🗃️ Raw JSON Data',
          'raw',
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto max-h-96">
            <pre className="text-xs whitespace-pre-wrap">
              {JSON.stringify(originalData, null, 2)}
            </pre>
          </div>,
          originalData
        )}
      </div>
    </Card>
  );
};

export default ExtractedInvoiceData;