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

interface PaymentTerms {
  amount: number | null;
  currency: string;
  frequency: 'monthly';
  due_days: number;
  late_fee: number | null;
  discount_terms: string | null;
}

interface InvoiceData {
  contract_title: string;
  client: Client;
  service_provider: ServiceProvider;
  payment_terms: PaymentTerms;
  services: Service[];
  special_terms: string;
  notes: string;
}

interface InvoiceProps {
  invoiceData: InvoiceData;
  amount: number;
}

const VintageInvoiceTemplate: React.FC<InvoiceProps> = ({ invoiceData, amount }) => {
  const invoiceNumber = 'INV-' + Math.floor(Math.random() * 10000);
  const invoiceDate = new Date();
  const dueDate = addDays(invoiceDate, invoiceData.payment_terms.due_days);

  const totalAmount = invoiceData.services.reduce((acc, service) => {
    return acc + (service.total_amount || 0);
  }, 0);

  return (
    <div className="max-w-4xl mx-auto bg-white shadow-lg border-2 border-gray-800 relative overflow-hidden">
      {/* Decorative Corner Elements */}
      <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-gray-800"></div>
      <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-gray-800"></div>
      <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-gray-800"></div>
      <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-gray-800"></div>

      <div className="relative p-12">
        {/* Professional Header */}
        <div className="text-center mb-10 border-b-2 border-gray-800 pb-6">
          <div className="flex justify-center items-center mb-4">
            <div className="w-1 h-6 bg-gray-800 mr-4"></div>
            <h1 className="text-4xl font-bold text-gray-900 tracking-wide" style={{fontFamily: 'serif'}}>
              INVOICE
            </h1>
            <div className="w-1 h-6 bg-gray-800 ml-4"></div>
          </div>
          <div className="text-gray-600 text-base tracking-wide" style={{fontFamily: 'serif'}}>
            — PROFESSIONAL SERVICES —
          </div>
          <div className="mt-4 text-gray-800 font-semibold text-lg">
            Invoice No. {invoiceNumber}
          </div>
        </div>

        {/* Date Information */}
        <div className="flex justify-between items-center mb-8">
          <div className="bg-gray-50 border border-gray-300 p-4 rounded-lg">
            <div className="text-gray-700 font-semibold mb-2" style={{fontFamily: 'serif'}}>Invoice Date</div>
            <div className="text-gray-900 text-base font-bold">{format(invoiceDate, 'MMMM dd, yyyy')}</div>
          </div>
          <div className="bg-gray-50 border border-gray-300 p-4 rounded-lg">
            <div className="text-gray-700 font-semibold mb-2" style={{fontFamily: 'serif'}}>Due Date</div>
            <div className="text-gray-900 text-base font-bold">{format(dueDate, 'MMMM dd, yyyy')}</div>
          </div>
        </div>

        {/* Company Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
          <div className="border border-gray-400 bg-gray-50 p-6 rounded-lg">
            <h3 className="text-lg font-bold text-gray-800 mb-4 border-b border-gray-400 pb-2" style={{fontFamily: 'serif'}}>
              FROM
            </h3>
            <div className="space-y-2">
              <p className="text-xl font-bold text-gray-900" style={{fontFamily: 'serif'}}>{invoiceData.service_provider.name}</p>
              <p className="text-gray-700">{invoiceData.service_provider.address}</p>
              <p className="text-gray-700">{invoiceData.service_provider.email}</p>
              <p className="text-gray-700">{invoiceData.service_provider.phone}</p>
            </div>
          </div>
          
          <div className="border border-gray-400 bg-gray-50 p-6 rounded-lg">
            <h3 className="text-lg font-bold text-gray-800 mb-4 border-b border-gray-400 pb-2" style={{fontFamily: 'serif'}}>
              BILL TO
            </h3>
            <div className="space-y-2">
              <p className="text-xl font-bold text-gray-900" style={{fontFamily: 'serif'}}>{invoiceData.client.name}</p>
              <p className="text-gray-700">{invoiceData.client.address}</p>
              {invoiceData.client.email && <p className="text-gray-700">{invoiceData.client.email}</p>}
              {invoiceData.client.phone && <p className="text-gray-700">{invoiceData.client.phone}</p>}
            </div>
          </div>
        </div>

        {/* Services Table with Professional Style */}
        <div className="mb-8">
          <h3 className="text-xl font-bold text-gray-800 mb-6 text-center" style={{fontFamily: 'serif'}}>
            — SERVICES —
          </h3>
          <div className="border-2 border-gray-400 rounded-lg overflow-hidden">
            <table className="w-full bg-white">
              <thead className="bg-gray-800 text-white">
                <tr>
                  <th className="px-6 py-4 text-left font-semibold" style={{fontFamily: 'serif'}}>Description</th>
                  <th className="px-6 py-4 text-center font-semibold" style={{fontFamily: 'serif'}}>Qty</th>
                  <th className="px-6 py-4 text-right font-semibold" style={{fontFamily: 'serif'}}>Rate</th>
                  <th className="px-6 py-4 text-right font-semibold" style={{fontFamily: 'serif'}}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {invoiceData.services.map((item, index) => (
                  <tr key={index} className="border-b border-gray-300">
                    <td className="px-6 py-4 text-gray-900" style={{fontFamily: 'serif'}}>
                      {item.description}
                    </td>
                    <td className="px-6 py-4 text-center text-gray-900">
                      {item.quantity || 1}
                    </td>
                    <td className="px-6 py-4 text-right text-gray-900">
                      {invoiceData.payment_terms.currency} {item.unit_price?.toFixed(2) || '0.00'}
                    </td>
                    <td className="px-6 py-4 text-right text-gray-900 font-semibold">
                      {invoiceData.payment_terms.currency} {item.total_amount?.toFixed(2) || '0.00'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Total Section */}
        <div className="flex justify-end mb-8">
          <div className="w-80 border-2 border-gray-400 bg-gray-50 rounded-lg p-6">
            <div className="text-center mb-4">
              <h4 className="text-lg font-bold text-gray-800" style={{fontFamily: 'serif'}}>TOTAL AMOUNT DUE</h4>
            </div>
            <div className="bg-gray-800 text-white p-4 rounded-lg text-center">
              <div className="text-2xl font-bold" style={{fontFamily: 'serif'}}>
                {invoiceData.payment_terms.currency} {totalAmount.toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        {/* Terms and Conditions */}
        <div className="border border-gray-400 bg-gray-50 p-6 rounded-lg mb-6">
          <h4 className="text-base font-bold text-gray-800 mb-3" style={{fontFamily: 'serif'}}>
            TERMS & CONDITIONS
          </h4>
          <div className="text-gray-700 space-y-2 text-sm">
            <p>• Payment is due within {invoiceData.payment_terms.due_days} days of invoice date</p>
            <p>• {invoiceData.special_terms}</p>
            {invoiceData.payment_terms.late_fee && (
              <p>• Late payment fee: {invoiceData.payment_terms.currency} {invoiceData.payment_terms.late_fee.toFixed(2)}</p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center border-t-2 border-gray-400 pt-6">
          <p className="text-gray-700 font-medium" style={{fontFamily: 'serif'}}>
            {invoiceData.notes || 'Thank you for your business.'}
          </p>
          <div className="mt-4 text-gray-600">
            <div className="w-24 h-0.5 bg-gray-400 mx-auto mb-2"></div>
            <p className="font-semibold" style={{fontFamily: 'serif'}}>
              {invoiceData.service_provider.name}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VintageInvoiceTemplate;