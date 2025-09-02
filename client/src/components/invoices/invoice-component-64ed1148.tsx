// COMPLETE REACT COMPONENT
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

interface Service {
  description: string;
  quantity: number;
  unit_price: number | null;
  total_amount: number | null;
  unit: string;
}

enum InvoiceFrequency {
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  ANNUALLY = 'annually',
}

interface PaymentTerms {
  amount: number | null;
  currency: string;
  frequency: InvoiceFrequency;
  due_days: number;
  late_fee: number | null;
  discount_terms: string | null;
}

interface InvoiceData {
  contract_title: string;
  contract_type: string;
  contract_number: string | null;
  client: Client;
  service_provider: Client;
  start_date: string; // Date string in YYYY-MM-DD format
  end_date: string; // Date string in YYYY-MM-DD format
  effective_date: string; // Date string in YYYY-MM-DD format
  payment_terms: PaymentTerms;
  services: Service[];
  invoice_frequency: InvoiceFrequency;
  first_invoice_date: string | null; // Date string in YYYY-MM-DD format
  next_invoice_date: string | null; // Date string in YYYY-MM-DD format
  special_terms: string;
  notes: string;
  confidence_score: number;
  extracted_at: string; // Date string in ISO format
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  invoiceNumber: string;
  invoiceDate: string; // Date string in YYYY-MM-DD format
}

const Invoice: React.FC<InvoiceProps> = ({ invoiceData, invoiceNumber, invoiceDate }) => {
  const dueDate = addDays(new Date(invoiceDate), invoiceData.payment_terms.due_days);
  const totalAmount = invoiceData.services.reduce((acc, service) => acc + (service.total_amount || 0), 0);

  const getStatusBadge = () => {
    const now = new Date();
    if (dueDate < now) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Overdue</span>;
    } else {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Paid</span>;
    }
  };

  return (
    <div className="bg-white shadow-sm rounded-lg p-6 print:p-0 font-sans text-gray-800">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 print:mb-4">
        <div>
          {/* Company Logo Placeholder */}
          <div className="w-32 h-16 bg-gray-100 rounded-md mb-2"></div>
          <p className="text-sm">{invoiceData.service_provider.name}</p>
          <p className="text-sm">{invoiceData.service_provider.address}</p>
          <p className="text-sm">{invoiceData.service_provider.email}</p>
          <p className="text-sm">{invoiceData.service_provider.phone}</p>
        </div>
        <div className="text-right">
          <h1 className="text-3xl font-bold text-blue-600 mb-2 print:text-xl">INVOICE</h1>
          <p className="text-sm">Invoice Number: {invoiceNumber}</p>
          <p className="text-sm">Invoice Date: {format(new Date(invoiceDate), 'MMMM dd, yyyy')}</p>
          <p className="text-sm">Status: {getStatusBadge()}</p>
        </div>
      </div>

      {/* Billing Information */}
      <div className="grid grid-cols-2 gap-4 mb-8 print:mb-4">
        <div>
          <h2 className="text-lg font-semibold mb-2 print:text-base">Bill To:</h2>
          <p className="text-sm">{invoiceData.client.name}</p>
          <p className="text-sm">{invoiceData.client.address}</p>
          <p className="text-sm">{invoiceData.client.email}</p>
          <p className="text-sm">{invoiceData.client.phone}</p>
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-2 print:text-base">Bill From:</h2>
          <p className="text-sm">{invoiceData.service_provider.name}</p>
          <p className="text-sm">{invoiceData.service_provider.address}</p>
          <p className="text-sm">{invoiceData.service_provider.email}</p>
          <p className="text-sm">{invoiceData.service_provider.phone}</p>
        </div>
      </div>

      {/* Services Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider print:text-xxs">
                Description
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-xxs">
                Quantity
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-xxs">
                Unit Price
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-xxs">
                Total
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {invoiceData.services.map((service, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 print:text-xxs">{service.description}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-900 print:text-xxs">{service.quantity} {service.unit}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-900 print:text-xxs">{service.unit_price ? `${invoiceData.payment_terms.currency} ${service.unit_price.toFixed(2)}` : '-'}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-900 print:text-xxs">{service.total_amount ? `${invoiceData.payment_terms.currency} ${service.total_amount.toFixed(2)}` : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Total Amount */}
      <div className="flex justify-end mt-4 print:mt-2">
        <div className="w-64">
          <div className="flex justify-between py-2 border-b border-gray-200">
            <span className="font-semibold text-sm print:text-xxs">Subtotal:</span>
            <span className="text-sm print:text-xxs">{invoiceData.payment_terms.currency} {totalAmount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="font-semibold text-sm print:text-xxs">Total:</span>
            <span className="text-lg font-bold text-blue-600 print:text-base">{invoiceData.payment_terms.currency} {totalAmount.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Payment Terms */}
      <div className="mt-8 print:mt-4">
        <h2 className="text-lg font-semibold mb-2 print:text-base">Payment Terms:</h2>
        <p className="text-sm">Due Date: <span className={dueDate < new Date() ? "text-red-600 font-semibold" : "font-semibold"}>{format(dueDate, 'MMMM dd, yyyy')}</span></p>
        <p className="text-sm">Payment Frequency: {invoiceData.payment_terms.frequency}</p>
        <p className="text-sm">Amount: {invoiceData.payment_terms.amount ? `${invoiceData.payment_terms.currency} ${invoiceData.payment_terms.amount.toFixed(2)}` : 'Variable'}</p>
        <p className="text-sm">Late Fee: {invoiceData.payment_terms.late_fee ? `${invoiceData.payment_terms.currency} ${invoiceData.payment_terms.late_fee.toFixed(2)}` : 'None'}</p>
        <p className="text-sm">Discount Terms: {invoiceData.payment_terms.discount_terms || 'None'}</p>
      </div>

      {/* Notes and Special Terms */}
      <div className="mt-8 print:mt-4">
        <h2 className="text-lg font-semibold mb-2 print:text-base">Notes:</h2>
        <p className="text-sm">{invoiceData.notes}</p>
      </div>
      <div className="mt-4 print:mt-2">
        <h2 className="text-lg font-semibold mb-2 print:text-base">Special Terms:</h2>
        <p className="text-sm">{invoiceData.special_terms}</p>
      </div>

      {/* Footer */}
      <div className="mt-12 pt-6 border-t border-gray-200 text-center text-sm text-gray-500 print:mt-6">
        <p>Make all checks payable to {invoiceData.service_provider.name}</p>
        <p>If you have any questions, please contact {invoiceData.service_provider.name} at {invoiceData.service_provider.email} or {invoiceData.service_provider.phone}</p>
        <p>&copy; {new Date().getFullYear()} {invoiceData.service_provider.name}. All rights reserved.</p>
      </div>
    </div>
  );
};

export default Invoice;