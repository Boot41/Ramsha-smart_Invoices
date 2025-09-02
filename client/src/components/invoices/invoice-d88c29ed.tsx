// COMPLETE REACT COMPONENT
import React from 'react';
import { format } from 'date-fns';

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

interface PaymentTerms {
  amount: number | null;
  currency: string;
  frequency: string | null;
  due_days: number | null;
  late_fee: number | null;
  discount_terms: string | null;
}

interface InvoiceData {
  contract_title: string;
  contract_type: string;
  contract_number: string | null;
  client: Client;
  service_provider: Client;
  start_date: string | null;
  end_date: string | null;
  effective_date: string;
  payment_terms: PaymentTerms;
  services: Service[];
  invoice_frequency: string | null;
  first_invoice_date: string | null;
  next_invoice_date: string | null;
  special_terms: string | null;
  notes: string;
  confidence_score: number;
  extracted_at: string;
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  invoiceNumber: string;
  invoiceDate: Date;
  dueDate: Date;
  status: 'paid' | 'unpaid' | 'overdue';
}

const Invoice: React.FC<InvoiceProps> = ({ invoiceData, invoiceNumber, invoiceDate, dueDate, status }) => {
  const calculateTotal = () => {
    let total = 0;
    invoiceData.services.forEach(service => {
      if (service.total_amount !== null) {
        total += service.total_amount;
      }
    });
    return total;
  };

  const totalAmount = calculateTotal();

  const getStatusBadge = () => {
    switch (status) {
      case 'paid':
        return <span className="bg-green-100 text-green-800 text-sm font-medium mr-2 px-2.5 py-0.5 rounded dark:bg-green-900 dark:text-green-300">Paid</span>;
      case 'unpaid':
        return <span className="bg-yellow-100 text-yellow-800 text-sm font-medium mr-2 px-2.5 py-0.5 rounded dark:bg-yellow-900 dark:text-yellow-300">Unpaid</span>;
      case 'overdue':
        return <span className="bg-red-100 text-red-800 text-sm font-medium mr-2 px-2.5 py-0.5 rounded dark:bg-red-900 dark:text-red-300">Overdue</span>;
      default:
        return null;
    }
  };

  return (
    <div className="font-sans antialiased bg-gray-100 print:bg-white">
      <div className="container mx-auto p-4 md:p-8">
        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          {/* Header */}
          <div className="bg-blue-600 text-white p-6 print:bg-white print:text-gray-800">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-semibold">Invoice</h1>
                <p className="text-sm">MR.K.Kuttan</p>
              </div>
              <div>
                {/* Company Logo Placeholder */}
                <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center print:hidden">
                  <span className="text-gray-500">Logo</span>
                </div>
              </div>
            </div>
          </div>

          {/* Invoice Details */}
          <div className="p-6">
            <div className="flex justify-between mb-4">
              <div>
                <p className="text-gray-600 text-sm">Invoice Number: <span className="font-medium">{invoiceNumber}</span></p>
                <p className="text-gray-600 text-sm">Invoice Date: <span className="font-medium">{format(invoiceDate, 'MMMM dd, yyyy')}</span></p>
                <p className="text-gray-600 text-sm">Status: {getStatusBadge()}</p>
              </div>
              <div className="text-right">
                <p className="text-gray-600 text-sm">Due Date:</p>
                <p className={`font-medium text-lg ${status === 'overdue' ? 'text-red-600' : 'text-blue-600'}`}>{format(dueDate, 'MMMM dd, yyyy')}</p>
              </div>
            </div>

            {/* Billing Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <h2 className="text-lg font-semibold mb-2">Bill To:</h2>
                <p className="text-gray-800">{invoiceData.client.name}</p>
                <p className="text-gray-600">{invoiceData.client.address}</p>
                {invoiceData.client.email && <p className="text-gray-600">{invoiceData.client.email}</p>}
                {invoiceData.client.phone && <p className="text-gray-600">{invoiceData.client.phone}</p>}
              </div>
              <div>
                <h2 className="text-lg font-semibold mb-2">Bill From:</h2>
                <p className="text-gray-800">{invoiceData.service_provider.name}</p>
                <p className="text-gray-600">{invoiceData.service_provider.address}</p>
                {invoiceData.service_provider.email && <p className="text-gray-600">{invoiceData.service_provider.email}</p>}
                {invoiceData.service_provider.phone && <p className="text-gray-600">{invoiceData.service_provider.phone}</p>}
              </div>
            </div>

            {/* Services Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full leading-normal">
                <thead>
                  <tr>
                    <th className="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Unit Price
                    </th>
                    <th className="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {invoiceData.services.map((service, index) => (
                    <tr key={index}>
                      <td className="px-5 py-5 border-b border-gray-200 bg-white text-sm">
                        <p className="text-gray-900 whitespace-no-wrap">{service.description}</p>
                      </td>
                      <td className="px-5 py-5 border-b border-gray-200 bg-white text-sm">
                        <p className="text-gray-900 whitespace-no-wrap">{service.quantity} {service.unit}</p>
                      </td>
                      <td className="px-5 py-5 border-b border-gray-200 bg-white text-sm">
                        <p className="text-gray-900 whitespace-no-wrap">{service.unit_price ? `${invoiceData.payment_terms.currency} ${service.unit_price.toFixed(2)}` : 'N/A'}</p>
                      </td>
                      <td className="px-5 py-5 border-b border-gray-200 bg-white text-sm">
                        <p className="text-gray-900 whitespace-no-wrap">{service.total_amount ? `${invoiceData.payment_terms.currency} ${service.total_amount.toFixed(2)}` : 'N/A'}</p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Total Amount */}
            <div className="flex justify-end mt-4">
              <div className="w-full md:w-1/3">
                <div className="bg-gray-100 p-4 rounded-md">
                  <p className="text-gray-700 font-semibold text-right">Subtotal: {invoiceData.payment_terms.currency} {totalAmount ? totalAmount.toFixed(2) : '0.00'}</p>
                  <p className="text-gray-700 font-semibold text-right">Total: {invoiceData.payment_terms.currency} {totalAmount ? totalAmount.toFixed(2) : '0.00'}</p>
                </div>
              </div>
            </div>

            {/* Notes and Terms */}
            <div className="mt-8">
              <h2 className="text-lg font-semibold mb-2">Notes:</h2>
              <p className="text-gray-700 text-sm">{invoiceData.notes}</p>
            </div>

            <div className="mt-4">
              <h2 className="text-lg font-semibold mb-2">Terms and Conditions:</h2>
              <p className="text-gray-700 text-sm">Payment is due within {invoiceData.payment_terms.due_days} days. Late fees may apply.</p>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-gray-200 p-6 text-center print:bg-white">
            <p className="text-gray-600 text-sm">
              Thank you for your business!
            </p>
            <p className="text-gray-600 text-sm">
              Payment Instructions: Please make payments to [Bank Name] - [Account Number]
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Invoice;