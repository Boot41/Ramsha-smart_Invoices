import React from 'react';
import { Card } from '../../components/ui';

const BotsList: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Bot Management</h1>
        <p className="text-gray-600 mt-2">Manage your automation bots</p>
      </div>
      
      <Card className="p-6">
        <p className="text-gray-500">Bot management features coming soon...</p>
      </Card>
    </div>
  );
};

export default BotsList;