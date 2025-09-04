import React from 'react';

interface LineItem {
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

interface LineItemTableProps {
  items?: LineItem[];
  style?: React.CSSProperties;
  className?: string;
}

export const LineItemTable: React.FC<LineItemTableProps> = ({
  items = [
    {
      description: 'Service Description',
      quantity: 1,
      unitPrice: 1000,
      total: 1000
    }
  ],
  style,
  className = ''
}) => {
  return (
    <div className={`line-item-table ${className}`} style={style}>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-2 font-semibold text-gray-700">Description</th>
              <th className="text-right py-3 px-2 font-semibold text-gray-700 w-20">Qty</th>
              <th className="text-right py-3 px-2 font-semibold text-gray-700 w-24">Unit Price</th>
              <th className="text-right py-3 px-2 font-semibold text-gray-700 w-24">Total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={index} className="border-b border-gray-100">
                <td className="py-3 px-2 text-gray-900">{item.description}</td>
                <td className="py-3 px-2 text-right text-gray-900">{item.quantity}</td>
                <td className="py-3 px-2 text-right text-gray-900">
                  ${item.unitPrice.toLocaleString()}
                </td>
                <td className="py-3 px-2 text-right text-gray-900 font-semibold">
                  ${item.total.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};