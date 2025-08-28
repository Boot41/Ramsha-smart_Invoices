import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '../components/shared';

// Import pages
import { Dashboard } from '../pages/dashboard';
import { InvoicesList, InvoiceTemplates, InvoiceScheduling } from '../pages/invoices';
import { ContractsList } from '../pages/contracts';
import { Login, Signup, EnterpriseSignup } from '../pages/auth';
import BotsList from '../pages/bots/BotsList';
import Marketplace from '../pages/marketplace/Marketplace';
import AdminDashboard from '../pages/admin/AdminDashboard';
import Settings from '../pages/settings/Settings';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />
      },
      {
        path: 'dashboard',
        element: <Dashboard />
      },
      {
        path: 'invoices',
        children: [
          {
            index: true,
            element: <InvoicesList />
          },
          {
            path: 'templates',
            element: <InvoiceTemplates />
          },
          {
            path: 'scheduling',
            element: <InvoiceScheduling />
          }
        ]
      },
      {
        path: 'contracts',
        element: <ContractsList />
      },
      {
        path: 'bots',
        element: <BotsList />
      },
      {
        path: 'marketplace',
        element: <Marketplace />
      },
      {
        path: 'admin',
        children: [
          {
            index: true,
            element: <AdminDashboard />
          },
          {
            path: 'users',
            element: <AdminDashboard />
          }
        ]
      },
      {
        path: 'settings',
        element: <Settings />
      }
    ]
  },
  // Auth routes (without layout)
  {
    path: '/auth',
    children: [
      {
        path: 'login',
        element: <Login />
      },
      {
        path: 'signup',
        element: <Signup />
      },
      {
        path: 'enterprise-signup',
        element: <EnterpriseSignup />
      }
    ]
  },
  // Catch all route
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />
  }
]);