// COMPLETE REACT COMPONENT
import React from 'react';
import moment from 'moment';

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
}

const Invoice: React.FC<InvoiceProps> = ({
  serviceProvider,
  clientName,
  service,
  amount,
  billingFrequency,
  invoiceData,
}) => {
  const invoiceNumber = Math.floor(Math.random() * 1000000);
  const invoiceDate = moment().format('MMMM D, YYYY');
  const dueDate = moment().add(30, 'days').format('MMMM D, YYYY');
  const nextInvoiceDate = invoiceData.next_invoice_date ? moment(invoiceData.next_invoice_date).format('MMMM D, YYYY') : 'N/A';

  const invoiceStatus = 'Paid'; // Example status

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'Paid':
        return 'bg-green-100 text-green-800';
      case 'Due':
        return 'bg-yellow-100 text-yellow-800';
      case 'Overdue':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="font-sans text-gray-800 antialiased print:bg-white print:text-black">
      <div className="max-w-4xl mx-auto p-8 bg-white shadow-sm border border-gray-200 rounded-lg">
        {/* Header */}
        <div className="flex justify-between items-center mb-6 print:mb-2">
          <div>
            <div className="h-12 w-32 bg-gray-200 rounded-md mb-2 print:hidden">
              {/* Company Logo Placeholder */}
            </div>
            <p className="text-sm text-gray-500">{serviceProvider}</p>
          </div>
          <div className="text-right">
            <h1 className="text-2xl font-semibold text-blue-600 print:text-black">Invoice</h1>
            <p className="text-sm text-gray-500">Invoice #: {invoiceNumber}</p>
            <p className="text-sm text-gray-500">Date: {invoiceDate}</p>
          </div>
        </div>

        {/* Bill To / Bill From */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 print:mb-2">
          <div>
            <h2 className="text-lg font-semibold mb-2 print:text-black">Bill To:</h2>
            <p>{clientName}</p>
            {/* Add client address details here */}
          </div>
          <div>
            <h2 className="text-lg font-semibold mb-2 print:text-black">Bill From:</h2>
            <p>{serviceProvider}</p>
            {/* Add service provider address details here */}
          </div>
        </div>

        {/* Invoice Items */}
        <div className="overflow-x-auto">
          <table className="min-w-full table-auto border-collapse border border-gray-200 print:border-black">
            <thead>
              <tr className="bg-gray-100 print:bg-gray-100">
                <th className="border border-gray-200 px-4 py-2 text-left print:border-black">Description</th>
                <th className="border border-gray-200 px-4 py-2 text-right print:border-black">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-gray-200 px-4 py-2 print:border-black">{service}</td>
                <td className="border border-gray-200 px-4 py-2 text-right print:border-black">${amount.toFixed(2)}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td className="border border-gray-200 px-4 py-2 font-semibold text-right print:border-black">Total:</td>
                <td className="border border-gray-200 px-4 py-2 text-right font-semibold print:border-black">${amount.toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* Payment Details */}
        <div className="mt-6 print:mt-2">
          <h2 className="text-lg font-semibold mb-2 print:text-black">Payment Details</h2>
          <p>
            Payment Terms: Due in 30 days
          </p>
          <p>
            Due Date: <span className={`font-semibold ${moment(dueDate).isBefore(moment()) ? 'text-red-600' : 'text-green-600'} print:text-black`}>{dueDate}</span>
          </p>
          <p>
            Next Invoice Date: {nextInvoiceDate}
          </p>
          <p>
            Billing Frequency: {billingFrequency}
          </p>
          <div className="mt-2">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(invoiceStatus)}`}>
              {invoiceStatus}
            </span>
          </div>
        </div>

        {/* Notes */}
        <div className="mt-6 print:mt-2">
          <h2 className="text-lg font-semibold mb-2 print:text-black">Notes</h2>
          <p className="text-sm text-gray-600">{invoiceData.notes || 'No notes.'}</p>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-gray-200 text-center text-sm text-gray-500 print:border-t-black">
          <p>Make all checks payable to {serviceProvider}</p>
          <p>If you have any questions, please contact us.</p>
        </div>
      </div>
    </div>
  );
};

export default Invoice;