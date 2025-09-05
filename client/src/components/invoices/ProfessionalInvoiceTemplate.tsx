import React from 'react';
import { invoicesAPI } from '../../../api/invoices';

interface ProfessionalInvoiceTemplateProps {
  invoice: Invoice;
  showActions?: boolean;
  onDownload?: (invoiceId: string) => void;
  onSend?: (invoiceId: string) => void;
  onStatusChange?: (invoiceId: string, status: Invoice['status']) => void;
}

const ProfessionalInvoiceTemplate: React.FC<ProfessionalInvoiceTemplateProps> = ({
  invoice,
  showActions = false,
  onDownload,
  onSend,
  onStatusChange
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const getStatusColor = (status: Invoice['status']) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      generated: 'bg-blue-100 text-blue-800',
      sent: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800',
      overdue: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-600'
    };
    return colors[status] || colors.draft;
  };

  const getServices = () => {
    if (invoice.invoice_data?.services) {
      return invoice.invoice_data.services;
    }
    if (invoice.invoice_data?.services_and_items) {
      return invoice.invoice_data.services_and_items;
    }
    // Fallback for single service
    return [{
      description: invoice.contract_title || 'Professional Services',
      quantity: 1,
      unit_price: invoice.subtotal,
      total_amount: invoice.subtotal,
      unit: 'service'
    }];
  };

  const services = getServices();

  return (
    <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 px-8 py-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">INVOICE</h1>
            <div className="text-blue-100">
              <p className="text-lg font-semibold">#{invoice.invoice_number}</p>
              <p className="text-sm">Date: {formatDate(invoice.invoice_date)}</p>
              <p className="text-sm">Due: {formatDate(invoice.due_date)}</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(invoice.status)}`}>
              {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
            </div>
            <div className="mt-4 text-blue-100">
              <p className="text-sm">Workflow: {invoice.workflow_id}</p>
              {invoice.contract_reference && (
                <p className="text-sm">Ref: {invoice.contract_reference}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="px-8 py-6">
        {/* Parties Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* From (Service Provider) */}
          <div>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">From</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-bold text-gray-900 mb-2">{invoice.service_provider_name}</h4>
              {invoice.service_provider_address && (
                <p className="text-gray-700 mb-1">{invoice.service_provider_address}</p>
              )}
              {invoice.service_provider_email && (
                <p className="text-gray-600 text-sm">{invoice.service_provider_email}</p>
              )}
              {invoice.service_provider_phone && (
                <p className="text-gray-600 text-sm">{invoice.service_provider_phone}</p>
              )}
            </div>
          </div>

          {/* To (Client) */}
          <div>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Bill To</h3>
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="text-lg font-bold text-gray-900 mb-2">{invoice.client_name}</h4>
              {invoice.client_address && (
                <p className="text-gray-700 mb-1">{invoice.client_address}</p>
              )}
              {invoice.client_email && (
                <p className="text-gray-600 text-sm">{invoice.client_email}</p>
              )}
              {invoice.client_phone && (
                <p className="text-gray-600 text-sm">{invoice.client_phone}</p>
              )}
            </div>
          </div>
        </div>

        {/* Contract Information */}
        {(invoice.contract_title || invoice.contract_type) && (
          <div className="mb-8 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Contract Details</h3>
            {invoice.contract_title && (
              <p className="text-gray-900 font-medium">{invoice.contract_title}</p>
            )}
            {invoice.contract_type && (
              <p className="text-gray-600 text-sm capitalize">{invoice.contract_type.replace('_', ' ')}</p>
            )}
          </div>
        )}

        {/* Services/Items Table */}
        <div className="mb-8">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Services & Items</h3>
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Qty
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rate
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {services.map((service: any, index: number) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {service.description}
                      </div>
                      {service.unit && service.unit !== 'service' && (
                        <div className="text-xs text-gray-500">Unit: {service.unit}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right text-sm text-gray-900">
                      {service.quantity || 1}
                    </td>
                    <td className="px-6 py-4 text-right text-sm text-gray-900">
                      {formatCurrency(service.unit_price || service.total_amount || 0, invoice.currency)}
                    </td>
                    <td className="px-6 py-4 text-right text-sm font-medium text-gray-900">
                      {formatCurrency(service.total_amount || service.unit_price || 0, invoice.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Totals */}
        <div className="flex justify-end mb-8">
          <div className="w-full max-w-md">
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Subtotal:</span>
                  <span className="text-gray-900 font-medium">
                    {formatCurrency(invoice.subtotal, invoice.currency)}
                  </span>
                </div>
                
                {invoice.tax_amount > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Tax:</span>
                    <span className="text-gray-900 font-medium">
                      {formatCurrency(invoice.tax_amount, invoice.currency)}
                    </span>
                  </div>
                )}
                
                <div className="border-t border-gray-200 pt-3">
                  <div className="flex justify-between">
                    <span className="text-base font-semibold text-gray-900">Total:</span>
                    <span className="text-xl font-bold text-blue-600">
                      {formatCurrency(invoice.total_amount, invoice.currency)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Payment Terms & Notes */}
        {invoice.invoice_data?.payment_terms?.payment_method && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Payment Information</h3>
            <p className="text-gray-700 text-sm capitalize">
              Payment Method: {invoice.invoice_data.payment_terms.payment_method.replace('_', ' ')}
            </p>
            {invoice.invoice_data.payment_terms.due_days && (
              <p className="text-gray-700 text-sm">
                Payment Terms: Net {invoice.invoice_data.payment_terms.due_days} days
              </p>
            )}
          </div>
        )}

        {/* Special Terms & Notes */}
        {(invoice.invoice_data?.special_terms || invoice.invoice_data?.notes) && (
          <div className="mb-6">
            {invoice.invoice_data.special_terms && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Special Terms</h3>
                <p className="text-gray-700 text-sm bg-yellow-50 p-3 rounded border-l-4 border-yellow-400">
                  {invoice.invoice_data.special_terms}
                </p>
              </div>
            )}
            
            {invoice.invoice_data.notes && (
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Notes</h3>
                <p className="text-gray-700 text-sm bg-blue-50 p-3 rounded border-l-4 border-blue-400">
                  {invoice.invoice_data.notes}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        {showActions && (onDownload || onSend || onStatusChange) && (
          <div className="border-t border-gray-200 pt-6">
            <div className="flex flex-wrap gap-3">
              {onDownload && (
                <button
                  onClick={() => onDownload(invoice.id)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download PDF
                </button>
              )}
              
              {onSend && (
                <button
                  onClick={() => onSend(invoice.id)}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Send Invoice
                </button>
              )}
              
              {onStatusChange && (
                <select
                  value={invoice.status}
                  onChange={(e) => onStatusChange(invoice.id, e.target.value as Invoice['status'])}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <option value="draft">Draft</option>
                  <option value="generated">Generated</option>
                  <option value="sent">Sent</option>
                  <option value="paid">Paid</option>
                  <option value="overdue">Overdue</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-50 px-8 py-4 border-t border-gray-200">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <div>
            Generated by {invoice.generated_by_agent}
            {invoice.human_reviewed && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                Human Reviewed
              </span>
            )}
          </div>
          <div>
            {invoice.confidence_score && (
              <span className="mr-4">
                Confidence: {(invoice.confidence_score * 100).toFixed(0)}%
              </span>
            )}
            Created: {formatDate(invoice.created_at)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfessionalInvoiceTemplate;