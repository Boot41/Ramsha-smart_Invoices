// COMPLETE REACT COMPONENT
import React from 'react';
import { format } from 'date-fns';

interface InvoiceData {
  contract_title: string;
  contract_type: string;
  contract_number: string | null;
  client: string | null;
  service_provider: string | null;
  start_date: string | null;
  end_date: string | null;
  effective_date: string | null;
  payment_terms: {
    amount: number;
    frequency: string;
  };
  services: string[];
  invoice_frequency: string | null;
  first_invoice_date: string | null;
  next_invoice_date: string | null;
  special_terms: string | null;
  notes: string | null;
  confidence_score: number;
  extracted_at: string;
  human_input_applied: boolean;
  human_input_timestamp: string;
}

interface InvoiceProps {
  serviceProvider: string;
  clientName: string;
  service: string;
  amount: number;
  billingFrequency: string;
  invoiceData: InvoiceData;
  invoiceNumber?: string;
  invoiceDate?: Date;
  dueDate?: Date;
  status?: 'paid' | 'unpaid' | 'overdue';
}

const Invoice: React.FC<InvoiceProps> = ({
  serviceProvider,
  clientName,
  service,
  amount,
  billingFrequency,
  invoiceData,
  invoiceNumber = 'INV-2024-001',
  invoiceDate = new Date(),
  dueDate = new Date(new Date().setDate(new Date().getDate() + 30)),
  status = 'unpaid',
}) => {
  const statusColors = {
    paid: 'bg-green-100 text-green-800',
    unpaid: 'bg-yellow-100 text-yellow-800',
    overdue: 'bg-red-100 text-red-800',
  };

  const formatDate = (date: Date): string => {
    return format(date, 'MMMM dd, yyyy');
  };

  return (
    <div className="container mx-auto p-4 print:p-0">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 print:mb-4">
        <div>
          {/* Company Logo Placeholder */}
          <div className="w-32 h-16 bg-gray-200 rounded-md mb-2 print:hidden">
            {/* Replace with your logo */}
          </div>
          <div className="text-sm text-gray-600">Service Provider</div>
          <div className="text-lg font-semibold">{serviceProvider}</div>
        </div>
        <div className="text-right">
          <h1 className="text-3xl font-bold text-gray-800 mb-2 print:text-2xl">Invoice</h1>
          <div className="text-sm text-gray-600">Invoice Number: {invoiceNumber}</div>
          <div className="text-sm text-gray-600">Date: {formatDate(invoiceDate)}</div>
        </div>
      </div>

      {/* Billing Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 print:mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2 print:text-lg">Bill To</h2>
          <div className="text-gray-700">
            <div>{clientName}</div>
            {/* Add client address and contact info here */}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2 print:text-lg">Bill From</h2>
          <div className="text-gray-700">
            <div>{serviceProvider}</div>
            {/* Add service provider address and contact info here */}
          </div>
        </div>
      </div>

      {/* Invoice Items */}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200 shadow-sm rounded-md print:shadow-none">
          <thead>
            <tr className="bg-gray-100">
              <th className="py-3 px-4 font-medium text-left text-gray-700">Description</th>
              <th className="py-3 px-4 font-medium text-right text-gray-700">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="py-3 px-4 border-t text-gray-700">{service}</td>
              <td className="py-3 px-4 border-t text-right text-gray-700">${amount.toFixed(2)}</td>
            </tr>
            {/* Add more invoice items here */}
          </tbody>
          <tfoot>
            <tr>
              <td className="py-3 px-4 font-medium text-right text-gray-700">Subtotal:</td>
              <td className="py-3 px-4 text-right text-gray-700">${amount.toFixed(2)}</td>
            </tr>
            <tr>
              <td className="py-3 px-4 font-medium text-right text-gray-700">Total:</td>
              <td className="py-3 px-4 text-right text-gray-700 font-semibold">${amount.toFixed(2)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Payment Information */}
      <div className="mt-8 print:mt-4">
        <h2 className="text-xl font-semibold text-gray-800 mb-2 print:text-lg">Payment Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-gray-700">
              <span className="font-medium">Payment Terms:</span> {billingFrequency}
            </div>
            <div className="text-gray-700">
              <span className="font-medium">Due Date:</span>{' '}
              <span className={dueDate < new Date() ? 'text-red-600 font-semibold' : ''}>{formatDate(dueDate)}</span>
            </div>
          </div>
          <div>
            <div className="text-gray-700">
              <span className="font-medium">Status:</span>{' '}
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[status]}`}>
                {status.toUpperCase()}
              </span>
            </div>
            {/* Add bank details or payment instructions here */}
          </div>
        </div>
      </div>

      {/* Notes and Terms */}
      <div className="mt-8 print:mt-4">
        <h2 className="text-xl font-semibold text-gray-800 mb-2 print:text-lg">Notes</h2>
        <div className="text-gray-700">{invoiceData.notes}</div>
      </div>

      <div className="mt-8 print:mt-4">
        <h2 className="text-xl font-semibold text-gray-800 mb-2 print:text-lg">Terms & Conditions</h2>
        <div className="text-gray-700">
          Payment is due within 30 days. Late payments may be subject to a late fee.
        </div>
      </div>

      {/* Footer */}
      <div className="mt-12 py-4 border-t border-gray-200 text-center text-gray-600 print:hidden">
        Thank you for your business!
      </div>
    </div>
  );
};

export default Invoice;