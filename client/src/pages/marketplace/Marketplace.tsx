import React from 'react';
import { Card } from '../../components/ui';

const Marketplace: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Marketplace</h1>
        <p className="text-gray-600 mt-2">Discover and install new features</p>
      </div>
      
      <Card className="p-6">
        <p className="text-gray-500">Marketplace features coming soon...</p>
      </Card>
    </div>
  );
};

export default Marketplace;