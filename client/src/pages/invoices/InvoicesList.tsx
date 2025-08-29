import React, { useState, useMemo } from 'react';
import { Card, Button, Badge, Table } from '../../components/ui';
import { mockInvoicesLegacy } from '../../data/mockData';
import { useInvoiceStore } from '../../../stores/invoiceStore';
import { createInvoiceFromContractData } from '../../utils/invoiceAdapter';
import { Plus, Filter, Download, Eye, Edit } from 'lucide-react';

const InvoicesList: React.FC = () => {
  const { invoiceGeneration, contractProcessing } = useInvoiceStore();

  const invoices = useMemo(() => {
    if (invoiceGeneration?.invoice_data) {
      const realInvoices = createInvoiceFromContractData(
        invoiceGeneration.invoice_data, 
        contractProcessing?.contract_name || 'Contract'
      );
      return realInvoices;
    }
    return mockInvoicesLegacy;
  }, [invoiceGeneration, contractProcessing]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'success';
      case 'sent':
        return 'warning';
      case 'overdue':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const columns = [
    {
      key: 'invoiceNumber',
      header: 'Invoice Number',
      render: (invoice: any) => (
        <div className="font-medium text-gray-900">{invoice.invoiceNumber}</div>
      )
    },
    {
      key: 'clientName',
      header: 'Client',
      render: (invoice: any) => (
        <div>
          <div className="font-medium text-gray-900">{invoice.clientName}</div>
          <div className="text-sm text-gray-500">{invoice.clientEmail}</div>
        </div>
      )
    },
    {
      key: 'amount',
      header: 'Amount',
      render: (invoice: any) => (
        <div className="font-medium text-gray-900">
          ${invoice.totalAmount.toLocaleString()}
        </div>
      )
    },
    {
      key: 'dueDate',
      header: 'Due Date',
      render: (invoice: any) => (
        <div className="text-gray-900">
          {new Date(invoice.dueDate).toLocaleDateString()}
        </div>
      )
    },
    {
      key: 'status',
      header: 'Status',
      render: (invoice: any) => (
        <Badge variant={getStatusColor(invoice.status)}>
          {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
        </Badge>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (invoice: any) => (
        <div className="flex space-x-2">
          <Button variant="ghost" size="sm">
            <Eye className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Edit className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Download className="w-4 h-4" />
          </Button>
        </div>
      )
    }
  ];

  const hasRealData = invoiceGeneration?.invoice_data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Invoices</h1>
          <p className="text-gray-600 mt-2">
            {hasRealData 
              ? `Showing invoice data extracted from ${contractProcessing?.contract_name || 'processed contract'}`
              : 'Manage and track all your invoices (showing mock data - process a contract to see real data)'}
          </p>
        </div>
        <div className="flex space-x-3 mt-4 sm:mt-0">
          <Button variant="outline">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Create Invoice
          </Button>
        </div>
      </div>

      <Card>
        <div className="p-6">
          <Table
            data={invoices}
            columns={columns}
            className="w-full"
          />
        </div>
      </Card>
    </div>
  );
};

export default InvoicesList;