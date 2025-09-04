import React from 'react';

interface HeaderProps {
  title?: string;
  companyName?: string;
  invoiceNumber?: string;
  date?: string;
  style?: React.CSSProperties;
  className?: string;
}

export const Header: React.FC<HeaderProps> = ({
  title = 'Invoice',
  companyName = 'Company Name',
  invoiceNumber = 'INV-001',
  date = new Date().toLocaleDateString(),
  style,
  className = ''
}) => {
  return (
    <div className={`invoice-header ${className}`} style={style}>
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{title}</h1>
          <p className="text-lg text-gray-700">{companyName}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">Invoice Number</p>
          <p className="text-lg font-semibold text-gray-900">{invoiceNumber}</p>
          <p className="text-sm text-gray-600 mt-2">Date</p>
          <p className="text-lg font-semibold text-gray-900">{date}</p>
        </div>
      </div>
    </div>
  );
};