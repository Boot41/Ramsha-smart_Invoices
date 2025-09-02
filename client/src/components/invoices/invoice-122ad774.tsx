// COMPLETE REACT COMPONENT
import React from 'react';
import { format, addDays } from 'date-fns';

interface InvoiceData {
  contract_title: string;
  contract_type: string;
  contract_number: string | null;
  client: {
    name: string;
    email: string | null;
    address: string;
    phone: string | null;
    tax_id: string | null;
    role: string;
  };
  service_provider: {
    name: string;
    email: string;
    address: string;
    phone: string;
    tax_id: string | null;
    role: string;
  };
  start_date: Date;
  end_date: Date;
  effective_date: Date;
  payment_terms: {
    amount: number;
    currency: string;
    frequency: string;
    due_days: number;
    late_fee: number | null;
    discount_terms: string | null;
  };
  services: {
    description: string;
    quantity: number;
    unit_price: number;
    total_amount: number;
    unit: string;
  }[];
  invoice_frequency: string;
  first_invoice_date: Date;
  next_invoice_date: Date;
  special_terms: string;
  notes: string;
  confidence_score: number;
  extracted_at: Date;
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  invoiceNumber: string;
  invoiceDate: Date;
}

const Invoice: React.FC<InvoiceProps> = ({ invoiceData, invoiceNumber, invoiceDate }) => {
  const dueDate = addDays(invoiceDate, invoiceData.payment_terms.due_days);
  const isOverdue = dueDate < new Date();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: invoiceData.payment_terms.currency,
    }).format(amount);
  };

  const totalAmount = invoiceData.services.reduce((sum, service) => sum + service.total_amount, 0);

  return (
    <div className="bg-white shadow-md rounded-md p-6 print:shadow-none print:border-none">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 print:mb-4">
        <div>
          {/* Company Logo Placeholder */}
          <div className="w-32 h-16 bg-gray-200 rounded-md mb-2 print:bg-white">
            {/* Replace with your logo */}
          </div>
          <p className="text-sm text-gray-600">{invoiceData.service_provider.name}</p>
          <p className="text-sm text-gray-600">{invoiceData.service_provider.address}</p>
          <p className="text-sm text-gray-600">Email: {invoiceData.service_provider.email}</p>
          <p className="text-sm text-gray-600">Phone: {invoiceData.service_provider.phone}</p>
        </div>
        <div className="text-right">
          <h1 className="text-3xl font-bold text-gray-800 mb-2 print:text-2xl">Invoice</h1>
          <p className="text-gray-600">Invoice Number: {invoiceNumber}</p>
          <p className="text-gray-600">Invoice Date: {format(invoiceDate, 'MMMM dd, yyyy')}</p>
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${isOverdue ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
            {isOverdue ? 'Overdue' : 'Paid'}
          </div>
        </div>
      </div>

      {/* Bill To / Bill From */}
      <div className="grid grid-cols-2 gap-4 mb-8 print:mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Bill To:</h2>
          <p className="text-gray-600">{invoiceData.client.name}</p>
          <p className="text-gray-600">{invoiceData.client.address}</p>
          {invoiceData.client.email && <p className="text-gray-600">Email: {invoiceData.client.email}</p>}
          {invoiceData.client.phone && <p className="text-gray-600">Phone: {invoiceData.client.phone}</p>}
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Bill From:</h2>
          <p className="text-gray-600">{invoiceData.service_provider.name}</p>
          <p className="text-gray-600">{invoiceData.service_provider.address}</p>
          <p className="text-gray-600">Email: {invoiceData.service_provider.email}</p>
          <p className="text-gray-600">Phone: {invoiceData.service_provider.phone}</p>
        </div>
      </div>

      {/* Services Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-700">
                Description
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-700">
                Quantity
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-700">
                Unit Price
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-700">
                Total
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {invoiceData.services.map((service, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 print:text-gray-900">{service.description}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-gray-900">{service.quantity} {service.unit}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-gray-900">{formatCurrency(service.unit_price)}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-gray-900">{formatCurrency(service.total_amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Total Amount */}
      <div className="mt-4 flex justify-end">
        <div className="w-1/2 text-right">
          <p className="text-lg font-semibold text-gray-700 print:text-base">Total: {formatCurrency(totalAmount)}</p>
        </div>
      </div>

      {/* Payment Terms */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Payment Terms:</h2>
        <p className="text-gray-600">
          Due Date: <span className={`${isOverdue ? 'text-red-600 font-semibold' : 'text-green-600 font-semibold'}`}>{format(dueDate, 'MMMM dd, yyyy')}</span>
        </p>
        <p className="text-gray-600">Amount: {formatCurrency(invoiceData.payment_terms.amount)}</p>
        <p className="text-gray-600">Frequency: {invoiceData.payment_terms.frequency}</p>
        {invoiceData.payment_terms.late_fee && <p className="text-gray-600">Late Fee: {invoiceData.payment_terms.late_fee}</p>}
        {invoiceData.payment_terms.discount_terms && <p className="text-gray-600">Discount Terms: {invoiceData.payment_terms.discount_terms}</p>}
      </div>

      {/* Notes and Special Terms */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Notes:</h2>
        <p className="text-gray-600">{invoiceData.notes}</p>
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Special Terms:</h2>
        <p className="text-gray-600">{invoiceData.special_terms}</p>
      </div>

      {/* Footer */}
      <div className="mt-12 pt-8 border-t border-gray-200 text-center print:border-t-0">
        <p className="text-sm text-gray-500">
          Thank you for your business!
        </p>
        <p className="text-xs text-gray-400">
          Payment Instructions: Please make payments to [Bank Name], [Account Number], [Swift Code]
        </p>
      </div>
    </div>
  );
};

export default Invoice;