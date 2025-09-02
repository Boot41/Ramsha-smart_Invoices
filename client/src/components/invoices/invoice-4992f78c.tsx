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
  quantity: number;
  unit_price: number | null;
  total_amount: number | null;
  unit: string;
}

interface PaymentTerms {
  amount: number | null;
  currency: string;
  frequency: string;
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
  start_date: string;
  end_date: string;
  effective_date: string;
  payment_terms: PaymentTerms;
  services: Service[];
  invoice_frequency: string;
  first_invoice_date: string;
  next_invoice_date: string;
  special_terms: string;
  notes: string;
  confidence_score: number;
  extracted_at: string;
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  invoiceNumber: string;
  invoiceDate: string;
}

const Invoice: React.FC<InvoiceProps> = ({ invoiceData, invoiceNumber, invoiceDate }) => {
  const { client, service_provider, services, payment_terms, next_invoice_date, special_terms, notes } = invoiceData;
  const dueDate = addDays(new Date(next_invoice_date), payment_terms.due_days);
  const totalAmount = services.reduce((acc, service) => acc + (service.total_amount || 0), 0);

  const getStatusBadge = () => {
    const now = new Date();
    if (dueDate < now) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Overdue</span>;
    } else {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Paid</span>;
    }
  };

  return (
    <div className="bg-white shadow-md rounded-md p-8 print:shadow-none print:p-0">
      {/* Header */}
      <div className="flex justify-between items-center mb-6 print:mb-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 print:text-xl">Invoice</h1>
          <p className="text-gray-500 text-sm print:text-xs">MR.K.Kuttan</p>
        </div>
        <div>
          {/* Company Logo Placeholder */}
          <div className="w-32 h-16 bg-gray-100 rounded-md print:hidden">
            {/* Replace with your logo */}
          </div>
        </div>
      </div>

      {/* Invoice Details */}
      <div className="grid grid-cols-2 gap-4 mb-6 print:mb-2">
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Invoice To:</h2>
          <p className="text-gray-600 text-sm print:text-xs">{client.name}</p>
          <p className="text-gray-600 text-sm print:text-xs">{client.address}</p>
          {client.email && <p className="text-gray-600 text-sm print:text-xs">{client.email}</p>}
          {client.phone && <p className="text-gray-600 text-sm print:text-xs">{client.phone}</p>}
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Invoice From:</h2>
          <p className="text-gray-600 text-sm print:text-xs">{service_provider.name}</p>
          <p className="text-gray-600 text-sm print:text-xs">{service_provider.address}</p>
          <p className="text-gray-600 text-sm print:text-xs">{service_provider.email}</p>
          <p className="text-gray-600 text-sm print:text-xs">{service_provider.phone}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6 print:mb-2">
        <div>
          <p className="text-gray-700 text-sm print:text-xs">
            Invoice Number: <span className="font-medium">{invoiceNumber}</span>
          </p>
          <p className="text-gray-700 text-sm print:text-xs">
            Invoice Date: <span className="font-medium">{format(new Date(invoiceDate), 'MMMM dd, yyyy')}</span>
          </p>
        </div>
        <div className="text-right">
          <p className="text-gray-700 text-sm print:text-xs">
            Status: {getStatusBadge()}
          </p>
          <p className="text-gray-700 text-sm print:text-xs">
            Due Date: <span className={`font-medium ${dueDate < new Date() ? 'text-red-600' : 'text-green-600'}`}>{format(dueDate, 'MMMM dd, yyyy')}</span>
          </p>
        </div>
      </div>

      {/* Services Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 print:bg-white">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-700">
                Description
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-700">
                Quantity
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-700">
                Unit Price
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider print:text-gray-700">
                Total
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {services.map((service, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 print:text-gray-900">{service.description}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-gray-900">{service.quantity} {service.unit}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-gray-900">{payment_terms.currency} {service.unit_price?.toFixed(2) || '0.00'}</td>
                <td className="px-6 py-4 text-right whitespace-nowrap text-sm text-gray-800 print:text-gray-900">{payment_terms.currency} {service.total_amount?.toFixed(2) || '0.00'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Total Amount */}
      <div className="mt-6 flex justify-end print:mt-2">
        <div className="w-64">
          <div className="flex justify-between items-center mb-2 print:mb-1">
            <span className="text-gray-700 font-medium print:text-gray-900">Subtotal:</span>
            <span className="text-gray-800 font-semibold print:text-gray-900">{payment_terms.currency} {totalAmount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between items-center mb-2 print:mb-1">
            <span className="text-gray-700 font-medium print:text-gray-900">Tax (0%):</span>
            <span className="text-gray-800 font-semibold print:text-gray-900">{payment_terms.currency} 0.00</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700 font-medium print:text-gray-900">Total:</span>
            <span className="text-2xl font-bold text-blue-600 print:text-xl">{payment_terms.currency} {totalAmount.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Notes and Terms */}
      <div className="mt-8 print:mt-2">
        <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Notes:</h2>
        <p className="text-gray-600 text-sm print:text-xs">{notes}</p>
      </div>

      <div className="mt-4 print:mt-1">
        <h2 className="text-lg font-semibold text-gray-700 mb-2 print:text-base">Special Terms:</h2>
        <p className="text-gray-600 text-sm print:text-xs">{special_terms}</p>
      </div>

      {/* Footer */}
      <div className="mt-12 pt-6 border-t border-gray-200 text-center print:mt-4 print:border-t-0">
        <p className="text-gray-500 text-xs print:text-xxs">
          Thank you for your business! Please make payments to:
        </p>
        <p className="text-gray-500 text-xs print:text-xxs">
          Bank: Example Bank | Account Number: 1234567890 | SWIFT Code: EXAMPLE
        </p>
      </div>
    </div>
  );
};

export default Invoice;