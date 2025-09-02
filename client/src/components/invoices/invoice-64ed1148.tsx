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
  start_date: string; // Assuming date is passed as string in 'YYYY-MM-DD' format
  end_date: string;   // Assuming date is passed as string in 'YYYY-MM-DD' format
  effective_date: string; // Assuming date is passed as string in 'YYYY-MM-DD' format
  payment_terms: {
    amount: number | null;
    currency: string;
    frequency: string;
    due_days: number;
    late_fee: number | null;
    discount_terms: string | null;
  };
  services: {
    description: string;
    quantity: number;
    unit_price: number | null;
    total_amount: number | null;
    unit: string;
  }[];
  invoice_frequency: string;
  first_invoice_date: string | null; // Assuming date is passed as string in 'YYYY-MM-DD' format
  next_invoice_date: string | null;  // Assuming date is passed as string in 'YYYY-MM-DD' format
  special_terms: string;
  notes: string;
  confidence_score: number;
  extracted_at: string; // Assuming date is passed as string
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  invoiceNumber: string;
  invoiceDate: Date;
}

const Invoice: React.FC<InvoiceProps> = ({ invoiceData, invoiceNumber, invoiceDate }) => {
  const dueDate = addDays(invoiceDate, invoiceData.payment_terms.due_days);
  const amountDue = invoiceData.services.reduce((acc, service) => acc + (service.total_amount || 0), 0);

  const getStatusBadge = () => {
    const isPastDue = dueDate < new Date();
    if (isPastDue) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Past Due</span>;
    } else {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Open</span>;
    }
  };

  return (
    <div className="bg-white shadow-md rounded-md p-8 font-sans text-gray-800 print:shadow-none print:border-none">
      {/* Header */}
      <div className="flex justify-between items-center mb-6 print:mb-2">
        <div>
          {/* Company Logo Placeholder */}
          <div className="w-32 h-16 bg-gray-200 rounded-md mb-2 print:hidden"></div>
          <h1 className="text-2xl font-bold">{invoiceData.service_provider.name}</h1>
          <p className="text-sm">{invoiceData.service_provider.address}</p>
          <p className="text-sm">Email: {invoiceData.service_provider.email}</p>
          <p className="text-sm">Phone: {invoiceData.service_provider.phone}</p>
        </div>
        <div className="text-right">
          <h2 className="text-3xl font-bold mb-2">Invoice</h2>
          <p>Invoice #: {invoiceNumber}</p>
          <p>Date: {format(invoiceDate, 'MMMM dd, yyyy')}</p>
          <p>Status: {getStatusBadge()}</p>
        </div>
      </div>

      {/* Bill To / Ship To */}
      <div className="grid grid-cols-2 gap-4 mb-6 print:mb-2">
        <div>
          <h3 className="text-lg font-semibold mb-1">Bill To:</h3>
          <p>{invoiceData.client.name}</p>
          <p>{invoiceData.client.address}</p>
          {invoiceData.client.email && <p>Email: {invoiceData.client.email}</p>}
          {invoiceData.client.phone && <p>Phone: {invoiceData.client.phone}</p>}
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-1">Service:</h3>
          <p>{invoiceData.contract_title}</p>
          <p>Frequency: {invoiceData.invoice_frequency}</p>
        </div>
      </div>

      {/* Services Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full table-auto border-collapse border border-gray-200">
          <thead>
            <tr className="bg-gray-100">
              <th className="border border-gray-200 px-4 py-2 text-left">Description</th>
              <th className="border border-gray-200 px-4 py-2 text-right">Quantity</th>
              <th className="border border-gray-200 px-4 py-2 text-right">Unit Price</th>
              <th className="border border-gray-200 px-4 py-2 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {invoiceData.services.map((service, index) => (
              <tr key={index}>
                <td className="border border-gray-200 px-4 py-2">{service.description}</td>
                <td className="border border-gray-200 px-4 py-2 text-right">{service.quantity} {service.unit}</td>
                <td className="border border-gray-200 px-4 py-2 text-right">{service.unit_price ? `${invoiceData.payment_terms.currency} ${service.unit_price.toFixed(2)}` : '-'}</td>
                <td className="border border-gray-200 px-4 py-2 text-right">{service.total_amount ? `${invoiceData.payment_terms.currency} ${service.total_amount.toFixed(2)}` : '-'}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={3} className="border border-gray-200 px-4 py-2 text-right font-semibold">Total:</td>
              <td className="border border-gray-200 px-4 py-2 text-right font-semibold">{invoiceData.payment_terms.currency} {amountDue.toFixed(2)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Payment Terms */}
      <div className="mt-6 print:mt-2">
        <h3 className="text-lg font-semibold mb-1">Payment Terms:</h3>
        <p>Due Date: <span className={`font-semibold ${dueDate < new Date() ? 'text-red-600' : 'text-blue-600'}`}>{format(dueDate, 'MMMM dd, yyyy')}</span></p>
        <p>Amount: {invoiceData.payment_terms.amount ? `${invoiceData.payment_terms.currency} ${invoiceData.payment_terms.amount.toFixed(2)}` : `${invoiceData.payment_terms.currency} ${amountDue.toFixed(2)}`}</p>
        <p>Please make payments to the account specified below.</p>
      </div>

      {/* Notes and Special Terms */}
      <div className="mt-6 print:mt-2">
        <h3 className="text-lg font-semibold mb-1">Notes:</h3>
        <p className="text-sm">{invoiceData.notes}</p>
      </div>

      <div className="mt-6 print:mt-2">
        <h3 className="text-lg font-semibold mb-1">Special Terms:</h3>
        <p className="text-sm">{invoiceData.special_terms}</p>
      </div>

      {/* Footer */}
      <div className="mt-8 pt-4 border-t border-gray-200 text-center text-sm text-gray-500 print:border-none">
        <p>Thank you for your business!</p>
        <p>Account Details: Bank Name, Account Number, Swift Code</p>
      </div>
    </div>
  );
};

export default Invoice;