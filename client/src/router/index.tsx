import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '../components/shared';

// Import pages
import { Dashboard } from '../pages/dashboard';
import { InvoicesList, InvoiceTemplates, InvoiceScheduling } from '../pages/invoices';
import InvoiceTemplatesList from '../pages/invoices/InvoiceTemplatesList';
import InvoicePreviewDemo from '../pages/invoices/InvoicePreviewDemo';
import { ContractsList } from '../pages/contracts';
import { Login, Signup, EnterpriseSignup } from '../pages/auth';
import BotsList from '../pages/bots/BotsList';
import Marketplace from '../pages/marketplace/Marketplace';
import AdminDashboard from '../pages/admin/AdminDashboard';
import Settings from '../pages/settings/Settings';
import WorkflowTracker from '../pages/workflow/WorkflowTracker';
import InteractiveWorkflow from '../pages/workflow/InteractiveWorkflow';

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
            path: 'templates-list',
            element: <InvoiceTemplatesList />
          },
          {
            path: 'scheduling',
            element: <InvoiceScheduling />
          },
          {
            path: 'preview-demo',
            element: <InvoicePreviewDemo />
          }
        ]
      },
      {
        path: 'contracts',
        element: <ContractsList />
      },
      {
        path: 'workflow',
        children: [
          {
            index: true,
            element: <InteractiveWorkflow />
          },
          {
            path: ':workflowId',
            element: <WorkflowTracker />
          }
        ]
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