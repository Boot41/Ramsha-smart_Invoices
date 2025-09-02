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
    email: string | null;
    address: string;
    phone: string | null;
    tax_id: string | null;
    role: string;
  };
  start_date: string; // Date string in 'yyyy-MM-dd' format
  end_date: string; // Date string in 'yyyy-MM-dd' format
  effective_date: string; // Date string in 'yyyy-MM-dd' format
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
  first_invoice_date: string; // Date string in 'yyyy-MM-dd' format
  next_invoice_date: string; // Date string in 'yyyy-MM-dd' format
  special_terms: string;
  notes: string;
  confidence_score: number;
  extracted_at: string; // Date string in 'yyyy-MM-ddTHH:mm:ss.SSSSSS' format
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  invoiceNumber: string;
  invoiceDate: Date;
}

const Invoice: React.FC<InvoiceProps> = ({ invoiceData, invoiceNumber, invoiceDate }) => {
  const dueDate = addDays(invoiceDate, invoiceData.payment_terms.due_days);
  const formattedDueDate = format(dueDate, 'MMMM dd, yyyy');
  const formattedInvoiceDate = format(invoiceDate, 'MMMM dd, yyyy');

  const isOverdue = dueDate < new Date();

  return (
    <div className="font-sans text-gray-800 antialiased bg-white shadow-md rounded-md overflow-hidden print:shadow-none print:rounded-none">
      {/* Header */}
      <div className="bg-blue-600 text-white py-6 px-8 print:bg-white print:text-gray-800">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold print:text-xl">Invoice</h1>
            <p className="text-sm">MR.K.Kuttan</p>
          </div>
          <div>
            {/* Company Logo Placeholder */}
            <div className="w-32 h-16 bg-gray-100 rounded-md shadow-sm print:hidden">
              {/* Replace with your logo */}
            </div>
          </div>
        </div>
      </div>

      {/* Invoice Details */}
      <div className="p-8 print:p-4">
        <div className="flex justify-between mb-6 print:mb-2">
          <div>
            <h2 className="text-lg font-semibold mb-2 print:text-base">Bill To:</h2>
            <p className="text-sm">{invoiceData.client.name}</p>
            <p className="text-sm">{invoiceData.client.address}</p>
            {invoiceData.client.email && <p className="text-sm">{invoiceData.client.email}</p>}
            {invoiceData.client.phone && <p className="text-sm">{invoiceData.client.phone}</p>}
          </div>
          <div className="text-right">
            <p className="text-sm">Invoice Number: {invoiceNumber}</p>
            <p className="text-sm">Invoice Date: {formattedInvoiceDate}</p>
            <p className="text-sm">Service: {invoiceData.contract_title}</p>
            <p className="text-sm">Billing Frequency: {invoiceData.invoice_frequency}</p>
            <p className="text-sm">
              Due Date: <span className={isOverdue ? 'text-red-500 font-semibold' : 'font-semibold'}>{formattedDueDate}</span>
            </p>
            <div className="mt-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${isOverdue ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                {isOverdue ? 'Overdue' : 'Paid'}
              </span>
            </div>
          </div>
        </div>

        {/* Services Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 print:bg-white">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-800">
                  Description
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-800">
                  Quantity
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-800">
                  Unit Price
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-800">
                  Total
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {invoiceData.services.map((service, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 print:text-gray-800">{service.description}</td>
                  <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-900 print:text-gray-800">{service.quantity}</td>
                  <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-900 print:text-gray-800">{invoiceData.payment_terms.currency} {service.unit_price.toFixed(2)}</td>
                  <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-900 print:text-gray-800">{invoiceData.payment_terms.currency} {service.total_amount.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Total Amount */}
        <div className="mt-6 flex justify-end print:mt-2">
          <div className="w-full sm:w-auto">
            <div className="bg-gray-100 p-4 rounded-md shadow-sm print:bg-white print:shadow-none">
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-700 print:text-gray-800">Subtotal:</span>
                <span className="text-sm font-medium text-gray-900 print:text-gray-800">{invoiceData.payment_terms.currency} {invoiceData.services.reduce((acc, service) => acc + Number(service.total_amount), 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-sm font-medium text-gray-700 print:text-gray-800">Total:</span>
                <span className="text-lg font-semibold text-gray-900 print:text-gray-800">{invoiceData.payment_terms.currency} {invoiceData.services.reduce((acc, service) => acc + Number(service.total_amount), 0).toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Notes and Terms */}
        <div className="mt-8 print:mt-4">
          <h2 className="text-lg font-semibold mb-2 print:text-base">Notes:</h2>
          <p className="text-sm text-gray-700 print:text-gray-800">{invoiceData.notes}</p>
        </div>

        <div className="mt-4 print:mt-2">
          <h2 className="text-lg font-semibold mb-2 print:text-base">Terms and Conditions:</h2>
          <p className="text-sm text-gray-700 print:text-gray-800">{invoiceData.special_terms}</p>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-100 py-4 px-8 text-sm text-gray-600 print:bg-white print:text-gray-700">
        <div className="flex justify-between">
          <div>
            <p>MR.K.Kuttan</p>
            <p>site No 152 Geethalayam OMH colong S.M. Road 1st main, T.Dasarahalli, Bangalore-57</p>
          </div>
          <div className="text-right">
            <p>Payment Instructions:</p>
            <p>Bank: Example Bank</p>
            <p>Account Number: 1234567890</p>
            <p>Routing Number: 0987654321</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Invoice;