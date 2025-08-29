import React, { useMemo } from "react";
import { useInvoiceStore } from "../../../stores/invoiceStore";
import { createInvoiceFromContractData } from "../../utils/invoiceAdapter";

const InvoiceTemplate = () => {
  const { invoiceGeneration, contractProcessing } = useInvoiceStore();

  const invoiceData = useMemo(() => {
    if (invoiceGeneration?.invoice_data) {
      const adaptedInvoices = createInvoiceFromContractData(
        invoiceGeneration.invoice_data,
        contractProcessing?.contract_name || 'Contract'
      );
      return adaptedInvoices[0]; // Get the first (and typically only) invoice
    }
    return null;
  }, [invoiceGeneration, contractProcessing]);

  if (!invoiceData) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-600 mb-4">No invoice data available.</p>
        <p className="text-sm text-gray-500">
          Process a contract to generate invoice data and view the template here.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 border rounded-xl shadow-md bg-white w-[800px] mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Invoice</h1>
        <p className="text-gray-600">#{invoiceData.invoiceNumber}</p>
      </div>

      {/* Client & Company Info */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div>
          <h2 className="font-semibold">Billed To:</h2>
          <p>{invoiceData.clientName}</p>
          <p>{invoiceData.clientEmail}</p>
        </div>
        <div className="text-right">
          <h2 className="font-semibold">From:</h2>
          <p>{invoiceData.companyName}</p>
          <p>{invoiceData.companyEmail}</p>
        </div>
      </div>

      {/* Items Table */}
      <table className="w-full border-collapse mb-6">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-2 text-left">Item</th>
            <th className="border p-2 text-right">Qty</th>
            <th className="border p-2 text-right">Price</th>
            <th className="border p-2 text-right">Total</th>
          </tr>
        </thead>
        <tbody>
          {invoiceData.items.map((item, index) => (
            <tr key={index}>
              <td className="border p-2">{item.description}</td>
              <td className="border p-2 text-right">{item.quantity}</td>
              <td className="border p-2 text-right">${item.unitPrice}</td>
              <td className="border p-2 text-right">
                ${item.totalPrice}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Summary */}
      <div className="flex justify-end">
        <div className="text-right">
          <p className="font-semibold">
            Subtotal: ${invoiceData.amount.toFixed(2)}
          </p>
          <p className="font-semibold">
            Tax: ${(invoiceData.taxAmount || 0).toFixed(2)}
          </p>
          <p className="text-xl font-bold">
            Total: ${invoiceData.totalAmount.toFixed(2)}
          </p>
        </div>
      </div>
    </div>
  );
};

export default InvoiceTemplate;
