import React from 'react';
import { Card } from '../../components/ui';
import { mockDashboardStats } from '../../data/mockData';
import {
  TrendingUp,
  FileText,
  AlertCircle,
  CheckCircle,
  DollarSign,
  Calendar
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const stats = [
    {
      name: 'Total Revenue',
      value: `$${mockDashboardStats.totalRevenue.toLocaleString()}`,
      icon: DollarSign,
      change: '+12.5%',
      changeType: 'positive'
    },
    {
      name: 'Total Invoices',
      value: mockDashboardStats.totalInvoices.toString(),
      icon: FileText,
      change: '+5.2%',
      changeType: 'positive'
    },
    {
      name: 'Pending Invoices',
      value: mockDashboardStats.pendingInvoices.toString(),
      icon: AlertCircle,
      change: '-2.1%',
      changeType: 'negative'
    },
    {
      name: 'Active Contracts',
      value: mockDashboardStats.activeContracts.toString(),
      icon: CheckCircle,
      change: '+8.3%',
      changeType: 'positive'
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome back! Here's what's happening with your invoices.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.name} className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                <p className={`text-sm mt-1 ${
                  stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {stat.change} from last month
                </p>
              </div>
              <div className={`p-3 rounded-full ${
                stat.changeType === 'positive' ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <stat.icon className={`w-6 h-6 ${
                  stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                }`} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Invoices</h3>
            <TrendingUp className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">INV-2024-001</p>
                <p className="text-sm text-gray-500">Acme Corporation</p>
              </div>
              <div className="text-right">
                <p className="font-medium text-gray-900">$2,700.00</p>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Paid
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">INV-2024-002</p>
                <p className="text-sm text-gray-500">Tech Solutions Inc</p>
              </div>
              <div className="text-right">
                <p className="font-medium text-gray-900">$1,930.50</p>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Pending
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">INV-2024-003</p>
                <p className="text-sm text-gray-500">Design Studio Pro</p>
              </div>
              <div className="text-right">
                <p className="font-medium text-gray-900">$3,504.00</p>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  Overdue
                </span>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Upcoming Events</h3>
            <Calendar className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Monthly rent invoice generation</p>
                <p className="text-sm text-gray-500">Tomorrow, 9:00 AM</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Payment reminder emails</p>
                <p className="text-sm text-gray-500">March 3, 10:00 AM</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Contract renewal review</p>
                <p className="text-sm text-gray-500">March 15, 2:00 PM</p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;