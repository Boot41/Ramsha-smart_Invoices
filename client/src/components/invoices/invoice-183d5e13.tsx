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
  service_provider: ServiceProvider;
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
  const totalAmount = invoiceData.services.reduce((sum, service) => sum + (service.total_amount || 0), 0);

  const getStatusBadge = () => {
    switch (status) {
      case 'paid':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Paid</span>;
      case 'unpaid':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Unpaid</span>;
      case 'overdue':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Overdue</span>;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6 print:shadow-none print:p-0">
      {/* Header */}
      <div className="flex justify-between items-start mb-8 print:mb-4">
        <div>
          {/* Company Logo Placeholder */}
          <div className="w-32 h-16 bg-gray-200 rounded-md mb-2 print:bg-white"></div>
          <h2 className="text-2xl font-bold text-gray-800 print:text-xl">{invoiceData.service_provider.name}</h2>
          <p className="text-gray-600 print:text-gray-600">{invoiceData.service_provider.address}</p>
          <p className="text-gray-600 print:text-gray-600">Email: {invoiceData.service_provider.email}</p>
          <p className="text-gray-600 print:text-gray-600">Phone: {invoiceData.service_provider.phone}</p>
        </div>
        <div className="text-right">
          <h1 className="text-4xl font-bold text-blue-600 mb-2 print:text-3xl print:text-blue-600">INVOICE</h1>
          <div className="flex items-center justify-end">
            <span className="mr-2 text-gray-700 print:text-gray-700">Status:</span>
            {getStatusBadge()}
          </div>
          <p className="text-gray-700 print:text-gray-700">Invoice Number: {invoiceNumber}</p>
          <p className="text-gray-700 print:text-gray-700">Invoice Date: {format(invoiceDate, 'MMMM dd, yyyy')}</p>
          <p className={`text-gray-700 print:text-gray-700 ${status === 'overdue' ? 'text-red-600 font-semibold' : ''}`}>
            Due Date: {format(dueDate, 'MMMM dd, yyyy')}
          </p>
        </div>
      </div>

      {/* Bill To / Bill From */}
      <div className="grid grid-cols-2 gap-4 mb-8 print:mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2 print:text-lg print:text-gray-700">Bill To:</h3>
          <p className="text-gray-600 print:text-gray-600">{invoiceData.client.name}</p>
          <p className="text-gray-600 print:text-gray-600">{invoiceData.client.address}</p>
          {invoiceData.client.email && <p className="text-gray-600 print:text-gray-600">Email: {invoiceData.client.email}</p>}
          {invoiceData.client.phone && <p className="text-gray-600 print:text-gray-600">Phone: {invoiceData.client.phone}</p>}
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2 print:text-lg print:text-gray-700">Bill From:</h3>
          <p className="text-gray-600 print:text-gray-600">{invoiceData.service_provider.name}</p>
          <p className="text-gray-600 print:text-gray-600">{invoiceData.service_provider.address}</p>
          <p className="text-gray-600 print:text-gray-600">Email: {invoiceData.service_provider.email}</p>
          <p className="text-gray-600 print:text-gray-600">Phone: {invoiceData.service_provider.phone}</p>
        </div>
      </div>

      {/* Services Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 print:bg-white">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider print:text-xs print:text-gray-500">
                Description
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-xs print:text-gray-500">
                Quantity
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-xs print:text-gray-500">
                Unit Price
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-xs print:text-gray-500">
                Total
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {invoiceData.services.map((service, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 print:text-sm print:text-gray-800">{service.description}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-sm print:text-gray-800">{service.quantity || '-'}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-sm print:text-gray-800">{service.unit_price ? `${invoiceData.payment_terms.currency} ${service.unit_price.toFixed(2)}` : '-'}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-sm print:text-gray-800">{service.total_amount ? `${invoiceData.payment_terms.currency} ${service.total_amount.toFixed(2)}` : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Total Amount */}
      <div className="mt-8 flex justify-end print:mt-4">
        <div className="w-64">
          <div className="flex justify-between items-center mb-2 print:mb-1">
            <span className="text-lg font-semibold text-gray-700 print:text-lg print:text-gray-700">Total:</span>
            <span className="text-lg font-bold text-blue-600 print:text-lg print:text-blue-600">{invoiceData.payment_terms.currency} {totalAmount.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Payment Terms */}
      <div className="mt-8 print:mt-4">
        <h3 className="text-lg font-semibold text-gray-700 mb-2 print:text-lg print:text-gray-700">Payment Terms:</h3>
        <p className="text-gray-600 print:text-gray-600">
          Amount: {invoiceData.payment_terms.amount ? `${invoiceData.payment_terms.currency} ${invoiceData.payment_terms.amount.toFixed(2)}` : 'N/A'}
        </p>
        <p className="text-gray-600 print:text-gray-600">Currency: {invoiceData.payment_terms.currency}</p>
        <p className="text-gray-600 print:text-gray-600">Frequency: {invoiceData.payment_terms.frequency || 'N/A'}</p>
        <p className="text-gray-600 print:text-gray-600">Due Days: {invoiceData.payment_terms.due_days || 'N/A'}</p>
        <p className="text-gray-600 print:text-gray-600">Late Fee: {invoiceData.payment_terms.late_fee || 'N/A'}</p>
        <p className="text-gray-600 print:text-gray-600">Discount Terms: {invoiceData.payment_terms.discount_terms || 'N/A'}</p>
      </div>

      {/* Notes */}
      <div className="mt-8 print:mt-4">
        <h3 className="text-lg font-semibold text-gray-700 mb-2 print:text-lg print:text-gray-700">Notes:</h3>
        <p className="text-gray-600 print:text-gray-600">{invoiceData.notes}</p>
      </div>

      {/* Terms and Conditions */}
      <div className="mt-8 print:mt-4">
        <h3 className="text-lg font-semibold text-gray-700 mb-2 print:text-lg print:text-gray-700">Terms and Conditions:</h3>
        <p className="text-gray-600 print:text-gray-600">
          Payment is due within {invoiceData.payment_terms.due_days || 30} days of the invoice date. Late payments may be subject to a late fee.
        </p>
      </div>

      {/* Footer */}
      <div className="mt-12 py-4 border-t border-gray-200 text-center text-gray-500 print:mt-6 print:border-t print:border-gray-200 print:text-center print:text-gray-500">
        <p>Thank you for your business!</p>
        <p>Payment Instructions: Please make payments to [Bank Name], [Account Number], [Routing Number]</p>
      </div>
    </div>
  );
};

export default Invoice;