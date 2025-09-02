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

type InvoiceFrequency = 'monthly';

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
  service_provider: ServiceProvider;
  start_date: Date | null;
  end_date: Date | null;
  effective_date: Date;
  payment_terms: PaymentTerms;
  services: Service[];
  invoice_frequency: InvoiceFrequency;
  first_invoice_date: Date | null;
  next_invoice_date: Date | null;
  special_terms: string;
  notes: string;
  confidence_score: number;
  extracted_at: Date;
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  amount: number;
  billingFrequency: InvoiceFrequency;
  service: string;
  client: string;
  serviceProvider: string;
}

const Invoice: React.FC<InvoiceProps> = ({ invoiceData, amount, billingFrequency, service, client, serviceProvider }) => {
  const invoiceNumber = 'INV-' + Math.floor(Math.random() * 10000);
  const invoiceDate = new Date();
  const dueDate = addDays(invoiceDate, invoiceData.payment_terms.due_days);

  const totalAmount = invoiceData.services.reduce((acc, service) => {
    return acc + (service.total_amount || 0);
  }, 0);

  const getStatusBadge = () => {
    const daysUntilDue = (dueDate.getTime() - new Date().getTime()) / (1000 * 3600 * 24);

    if (daysUntilDue < 0) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Overdue</span>;
    } else if (daysUntilDue <= 7) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Due Soon</span>;
    } else {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Open</span>;
    }
  };


  return (
    <div className="bg-white shadow-md rounded-lg p-6 print:shadow-none print:p-0">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 print:mb-4">
        <div>
          <div className="text-2xl font-bold text-gray-800">{serviceProvider}</div>
          <div className="text-sm text-gray-500">{invoiceData.service_provider.address}</div>
          <div className="text-sm text-gray-500">Email: {invoiceData.service_provider.email}</div>
          <div className="text-sm text-gray-500">Phone: {invoiceData.service_provider.phone}</div>
        </div>
        <div>
          {/* Company Logo Placeholder */}
          <div className="w-32 h-16 bg-gray-100 rounded-md flex items-center justify-center text-gray-400">
            Logo
          </div>
        </div>
      </div>

      {/* Invoice Details */}
      <div className="grid grid-cols-2 gap-4 mb-6 print:mb-3">
        <div>
          <div className="text-gray-700 font-semibold mb-1">Bill To:</div>
          <div className="text-gray-800">{client}</div>
          <div className="text-gray-500">{invoiceData.client.address}</div>
          {invoiceData.client.email && <div className="text-gray-500">Email: {invoiceData.client.email}</div>}
          {invoiceData.client.phone && <div className="text-gray-500">Phone: {invoiceData.client.phone}</div>}
        </div>
        <div>
          <div className="text-gray-700 font-semibold mb-1">Invoice Details:</div>
          <div className="flex justify-between">
            <div className="text-gray-800">Invoice Number:</div>
            <div className="text-gray-800">{invoiceNumber}</div>
          </div>
          <div className="flex justify-between">
            <div className="text-gray-800">Invoice Date:</div>
            <div className="text-gray-800">{format(invoiceDate, 'MMMM dd, yyyy')}</div>
          </div>
          <div className="flex justify-between">
            <div className="text-gray-800">Due Date:</div>
            <div className={`text-gray-800 font-semibold ${dueDate < new Date() ? 'text-red-600' : ''}`}>{format(dueDate, 'MMMM dd, yyyy')}</div>
          </div>
          <div className="flex justify-between">
            <div className="text-gray-800">Status:</div>
            <div>{getStatusBadge()}</div>
          </div>
        </div>
      </div>

      {/* Services Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {invoiceData.services.map((item, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{item.description}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 text-right">{invoiceData.payment_terms.currency} {item.total_amount?.toFixed(2) || '0.00'}</td>
              </tr>
            ))}
            <tr>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-800">Total</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-800 text-right">{invoiceData.payment_terms.currency} {totalAmount.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Payment Terms */}
      <div className="mt-6 print:mt-3">
        <div className="text-gray-700 font-semibold mb-1">Payment Terms:</div>
        <div className="text-gray-500">
          Amount: {invoiceData.payment_terms.currency} {amount.toFixed(2)} due in {invoiceData.payment_terms.due_days} days.
        </div>
        {invoiceData.payment_terms.late_fee && (
          <div className="text-gray-500">Late fee: {invoiceData.payment_terms.currency} {invoiceData.payment_terms.late_fee.toFixed(2)}</div>
        )}
        {invoiceData.payment_terms.discount_terms && (
          <div className="text-gray-500">Discount: {invoiceData.payment_terms.discount_terms}</div>
        )}
      </div>

      {/* Terms and Conditions */}
      <div className="mt-6 print:mt-3">
        <div className="text-gray-700 font-semibold mb-1">Terms & Conditions:</div>
        <div className="text-gray-500">{invoiceData.special_terms}</div>
      </div>

      {/* Notes */}
      <div className="mt-6 print:mt-3">
        <div className="text-gray-700 font-semibold mb-1">Notes:</div>
        <div className="text-gray-500">{invoiceData.notes}</div>
      </div>

      {/* Footer */}
      <div className="mt-8 pt-4 border-t border-gray-200 text-center text-gray-500 print:mt-4">
        <p>Make all checks payable to {serviceProvider}</p>
        <p>Thank you for your business!</p>
      </div>
    </div>
  );
};

export default Invoice;