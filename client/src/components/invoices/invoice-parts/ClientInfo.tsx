import React from 'react';

interface ClientInfoProps {
  clientName?: string;
  clientAddress?: string;
  providerName?: string;
  providerAddress?: string;
  style?: React.CSSProperties;
  className?: string;
}

export const ClientInfo: React.FC<ClientInfoProps> = ({
  clientName = 'Client Name',
  clientAddress = 'Client Address',
  providerName = 'Service Provider',
  providerAddress = 'Provider Address',
  style,
  className = ''
}) => {
  return (
    <div className={`client-info ${className}`} style={style}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-2">
            Bill To
          </h3>
          <div className="text-gray-900">
            <p className="font-semibold">{clientName}</p>
            <p className="text-sm text-gray-700 mt-1 whitespace-pre-line">{clientAddress}</p>
          </div>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-2">
            From
          </h3>
          <div className="text-gray-900">
            <p className="font-semibold">{providerName}</p>
            <p className="text-sm text-gray-700 mt-1 whitespace-pre-line">{providerAddress}</p>
          </div>
        </div>
      </div>
    </div>
  );
};