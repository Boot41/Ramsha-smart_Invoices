import React from 'react';
import { Card } from '../../components/ui';

const AdminDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">Administrative controls and settings</p>
      </div>
      
      <Card className="p-6">
        <p className="text-gray-500">Admin dashboard features coming soon...</p>
      </Card>
    </div>
  );
};

export default AdminDashboard;