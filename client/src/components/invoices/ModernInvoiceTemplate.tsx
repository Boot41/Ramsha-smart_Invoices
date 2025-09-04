import React from 'react';
import { format, addDays } from 'date-fns';

interface Client {
  name: string;
  email: string | null;
  address: string;
  phone: string | null;
  tax_id: string | null;
  role: string;
}

interface ServiceProvider {
  name: string;
  email: string;
  address: string;
  phone: string;
  tax_id: string | null;
  role: string;
}

interface Service {
  description: string;
  quantity: number | null;
  unit_price: number | null;
  total_amount: number | null;
  unit: string | null;
}

interface PaymentTerms {
  amount: number | null;
  currency: string;
  frequency: 'monthly';
  due_days: number;
  late_fee: number | null;
  discount_terms: string | null;
}

interface InvoiceData {
  contract_title: string;
  client: Client;
  service_provider: ServiceProvider;
  payment_terms: PaymentTerms;
  services: Service[];
  special_terms: string;
  notes: string;
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  amount: number;
}

const ModernInvoiceTemplate: React.FC<InvoiceProps> = ({ invoiceData, amount }) => {
  const invoiceNumber = 'INV-' + Math.floor(Math.random() * 10000);
  const invoiceDate = new Date();
  const dueDate = addDays(invoiceDate, invoiceData.payment_terms.due_days);

  const totalAmount = invoiceData.services.reduce((acc, service) => {
    return acc + (service.total_amount || 0);
  }, 0);

  const taxAmount = totalAmount * 0.1; // 10% tax
  const finalAmount = totalAmount + taxAmount;

  return (
    <div className="max-w-4xl mx-auto bg-white shadow-lg border border-gray-200">
      {/* Professional Header */}
      <div className="bg-white border-b-2 border-blue-600 p-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">INVOICE</h1>
            <p className="text-blue-600 text-lg font-semibold">#{invoiceNumber}</p>
          </div>
          <div className="text-right">
            <div className="w-20 h-20 bg-gray-50 border-2 border-gray-200 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl text-gray-400">LOGO</span>
            </div>
            <p className="text-gray-600 font-medium">Date: {format(invoiceDate, 'MMM dd, yyyy')}</p>
            <p className="text-gray-600 font-medium">Due: {format(dueDate, 'MMM dd, yyyy')}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        {/* Company and Client Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div>
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-blue-600 uppercase tracking-wide mb-4">
                From
              </h3>
              <p className="font-bold text-xl text-gray-900 mb-2">{invoiceData.service_provider.name}</p>
              <p className="text-gray-600 mb-1">{invoiceData.service_provider.address}</p>
              <p className="text-gray-600 mb-1">{invoiceData.service_provider.email}</p>
              <p className="text-gray-600">{invoiceData.service_provider.phone}</p>
            </div>
          </div>
          
          <div>
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-blue-600 uppercase tracking-wide mb-4">
                Bill To
              </h3>
              <p className="font-bold text-xl text-gray-900 mb-2">{invoiceData.client.name}</p>
              <p className="text-gray-600 mb-1">{invoiceData.client.address}</p>
              {invoiceData.client.email && <p className="text-gray-600 mb-1">{invoiceData.client.email}</p>}
              {invoiceData.client.phone && <p className="text-gray-600">{invoiceData.client.phone}</p>}
            </div>
          </div>
        </div>

        {/* Services Table */}
        <div className="mb-8">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-blue-600">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Description</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-white">Qty</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-white">Rate</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-white">Amount</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {invoiceData.services.map((item, index) => (
                  <tr key={index} className="border-b border-gray-200">
                    <td className="px-6 py-4 text-gray-900">{item.description}</td>
                    <td className="px-6 py-4 text-right text-gray-900">{item.quantity || 1}</td>
                    <td className="px-6 py-4 text-right text-gray-900">
                      {invoiceData.payment_terms.currency} {item.unit_price?.toFixed(2) || '0.00'}
                    </td>
                    <td className="px-6 py-4 text-right text-gray-900 font-semibold">
                      {invoiceData.payment_terms.currency} {item.total_amount?.toFixed(2) || '0.00'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Summary */}
        <div className="flex justify-end mb-8">
          <div className="w-full md:w-96">
            <div className="border border-gray-200 rounded-lg p-6">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal:</span>
                  <span className="text-gray-900 font-medium">{invoiceData.payment_terms.currency} {totalAmount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Tax (10%):</span>
                  <span className="text-gray-900 font-medium">{invoiceData.payment_terms.currency} {taxAmount.toFixed(2)}</span>
                </div>
                <div className="border-t border-gray-300 pt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-gray-900">Total:</span>
                    <span className="text-2xl font-bold text-blue-600">{invoiceData.payment_terms.currency} {finalAmount.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Payment Terms & Notes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="border border-gray-200 rounded-lg p-6">
            <h4 className="text-sm font-semibold text-blue-600 uppercase tracking-wide mb-3">
              Payment Terms
            </h4>
            <p className="text-gray-700 text-sm">Payment is due within {invoiceData.payment_terms.due_days} days of invoice date.</p>
            {invoiceData.payment_terms.late_fee && (
              <p className="text-gray-700 text-sm mt-2">Late fee: {invoiceData.payment_terms.currency} {invoiceData.payment_terms.late_fee.toFixed(2)}</p>
            )}
          </div>
          
          <div className="border border-gray-200 rounded-lg p-6">
            <h4 className="text-sm font-semibold text-blue-600 uppercase tracking-wide mb-3">
              Notes
            </h4>
            <p className="text-gray-700 text-sm">{invoiceData.notes || 'Thank you for your business!'}</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 text-center py-6">
        <p className="text-gray-600">Thank you for choosing {invoiceData.service_provider.name}</p>
        <p className="text-sm text-gray-500 mt-1">Invoice generated on {format(new Date(), 'PPP')}</p>
      </div>
    </div>
  );
};

export default ModernInvoiceTemplate;