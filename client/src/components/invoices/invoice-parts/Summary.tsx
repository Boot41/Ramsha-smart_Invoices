import React from 'react';

interface SummaryProps {
  subtotal?: number;
  tax?: number;
  total?: number;
  currency?: string;
  style?: React.CSSProperties;
  className?: string;
}

export const Summary: React.FC<SummaryProps> = ({
  subtotal = 1000,
  tax = 0,
  total = 1000,
  currency = 'USD',
  style,
  className = ''
}) => {
  return (
    <div className={`invoice-summary ${className}`} style={style}>
      <div className="w-full max-w-sm ml-auto">
        <div className="space-y-2">
          <div className="flex justify-between py-2">
            <span className="text-gray-700">Subtotal:</span>
            <span className="text-gray-900 font-medium">
              ${subtotal.toLocaleString()}
            </span>
          </div>
          
          {tax > 0 && (
            <div className="flex justify-between py-2">
              <span className="text-gray-700">Tax:</span>
              <span className="text-gray-900 font-medium">
                ${tax.toLocaleString()}
              </span>
            </div>
          )}
          
          <div className="border-t border-gray-200 pt-2">
            <div className="flex justify-between py-2">
              <span className="text-lg font-semibold text-gray-900">Total:</span>
              <span className="text-lg font-bold text-gray-900">
                ${total.toLocaleString()} {currency}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};