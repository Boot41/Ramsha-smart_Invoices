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

const MinimalistInvoiceTemplate: React.FC<InvoiceProps> = ({ invoiceData }) => {
  const invoiceNumber = 'INV-' + Math.floor(Math.random() * 10000);
  const invoiceDate = new Date();
  const dueDate = addDays(invoiceDate, invoiceData.payment_terms.due_days);

  const totalAmount = invoiceData.services.reduce((acc, service) => {
    return acc + (service.total_amount || 0);
  }, 0);

  return (
    <div className="max-w-4xl mx-auto bg-white shadow-lg border border-gray-200">
      {/* Clean Professional Header */}
      <div className="border-b-2 border-gray-900 p-8">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 tracking-wide">INVOICE</h1>
          </div>
          <div className="text-right">
            <div className="text-gray-900 font-semibold mb-2">#{invoiceNumber}</div>
            <div className="text-gray-600">{format(invoiceDate, 'MMMM dd, yyyy')}</div>
            <div className="text-gray-600">Due: {format(dueDate, 'MMMM dd, yyyy')}</div>
          </div>
        </div>
      </div>

      <div className="p-8">
        {/* Professional Info Layout */}
        <div className="grid grid-cols-2 gap-12 mb-12">
          <div>
            <div className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4 pb-2 border-b border-gray-300">From</div>
            <div className="space-y-2">
              <p className="text-lg font-semibold text-gray-900">{invoiceData.service_provider.name}</p>
              <p className="text-sm text-gray-700">{invoiceData.service_provider.address}</p>
              <p className="text-sm text-gray-700">{invoiceData.service_provider.email}</p>
              <p className="text-sm text-gray-700">{invoiceData.service_provider.phone}</p>
            </div>
          </div>
          
          <div>
            <div className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4 pb-2 border-b border-gray-300">Bill To</div>
            <div className="space-y-2">
              <p className="text-lg font-semibold text-gray-900">{invoiceData.client.name}</p>
              <p className="text-sm text-gray-700">{invoiceData.client.address}</p>
              {invoiceData.client.email && <p className="text-sm text-gray-700">{invoiceData.client.email}</p>}
              {invoiceData.client.phone && <p className="text-sm text-gray-700">{invoiceData.client.phone}</p>}
            </div>
          </div>
        </div>

        {/* Professional Services Table */}
        <div className="mb-12">
          <div className="border border-gray-300 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-800">Description</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-800">Qty</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-800">Rate</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-800">Amount</th>
                </tr>
              </thead>
              <tbody>
                {invoiceData.services.map((item, index) => (
                  <tr key={index} className="border-b border-gray-200">
                    <td className="px-6 py-4 text-gray-900">{item.description}</td>
                    <td className="px-6 py-4 text-center text-gray-900">{item.quantity || 1}</td>
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

        {/* Professional Total */}
        <div className="flex justify-end mb-10">
          <div className="w-80 border border-gray-300 rounded-lg p-6 bg-gray-50">
            <div className="flex justify-between items-center pb-3 border-b border-gray-300">
              <span className="text-lg font-semibold text-gray-800">Total Amount Due</span>
              <span className="text-2xl font-bold text-gray-900">
                {invoiceData.payment_terms.currency} {totalAmount.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Payment Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
          <div className="border border-gray-200 rounded-lg p-6">
            <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4 pb-2 border-b border-gray-300">Payment Terms</h4>
            <div className="space-y-2 text-sm text-gray-700">
              <p>Payment due within {invoiceData.payment_terms.due_days} days</p>
              <p>Due Date: {format(dueDate, 'MMMM dd, yyyy')}</p>
              {invoiceData.payment_terms.late_fee && (
                <p>Late Fee: {invoiceData.payment_terms.currency} {invoiceData.payment_terms.late_fee.toFixed(2)}</p>
              )}
            </div>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-6">
            <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4 pb-2 border-b border-gray-300">Notes</h4>
            <p className="text-sm text-gray-700">
              {invoiceData.notes || 'Thank you for your business.'}
            </p>
          </div>
        </div>

        {/* Professional Footer */}
        <div className="border-t-2 border-gray-300 pt-6">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Invoice generated on {format(new Date(), 'MMMM dd, yyyy')}
            </div>
            <div className="text-sm font-medium text-gray-800">
              {invoiceData.service_provider.name}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MinimalistInvoiceTemplate;