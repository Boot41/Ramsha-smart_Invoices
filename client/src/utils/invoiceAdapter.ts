import type { ContractInvoiceData } from '@client-api/contracts';

export interface AdaptedInvoiceData {
  id: string;
  invoiceNumber: string;
  clientName: string;
  clientEmail?: string;
  clientAddress?: {
    street?: string;
    city?: string;
    state?: string;
    zipCode?: string;
    country?: string;
  };
  amount: number;
  currency: string;
  dueDate: string;
  issueDate: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue';
  items: {
    id: string;
    description: string;
    quantity: number;
    unitPrice: number;
    totalPrice: number;
  }[];
  notes?: string;
  taxRate?: number;
  taxAmount?: number;
  totalAmount: number;
  paymentTerms?: string;
  createdAt: string;
  updatedAt: string;
  companyName?: string;
  companyEmail?: string;
  tax?: number;
  total: number;
}

export function adaptContractInvoiceData(
  contractInvoiceData: ContractInvoiceData,
  contractName: string
): AdaptedInvoiceData {
  const currentDate = new Date().toISOString();
  const dueDate = contractInvoiceData.next_invoice_date || 
    contractInvoiceData.first_invoice_date || 
    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

  const services = contractInvoiceData.services || [];
  const totalAmount = services.reduce((sum, service) => sum + (service.total_amount || 0), 0);
  const taxAmount = totalAmount * 0.1; // Default 10% tax
  const finalTotal = totalAmount + taxAmount;

  const items = services.map((service, index) => ({
    id: `item-${index + 1}`,
    description: service.description,
    quantity: service.quantity || 1,
    unitPrice: service.unit_price || 0,
    totalPrice: service.total_amount || (service.quantity || 1) * (service.unit_price || 0)
  }));

  return {
    id: `inv-${Date.now()}`,
    invoiceNumber: contractInvoiceData.contract_number || `INV-${Date.now()}`,
    clientName: contractInvoiceData.client?.name || 'Unknown Client',
    clientEmail: contractInvoiceData.client?.email,
    clientAddress: contractInvoiceData.client?.address ? {
      street: contractInvoiceData.client.address,
      city: '',
      state: '',
      zipCode: '',
      country: ''
    } : undefined,
    amount: totalAmount,
    currency: contractInvoiceData.payment_terms?.currency || 'USD',
    dueDate: dueDate.split('T')[0],
    issueDate: currentDate.split('T')[0],
    status: 'draft' as const,
    items,
    notes: contractInvoiceData.notes || contractInvoiceData.special_terms,
    taxRate: 0.1,
    taxAmount,
    totalAmount: finalTotal,
    paymentTerms: contractInvoiceData.payment_terms?.frequency || 'Net 30',
    createdAt: currentDate,
    updatedAt: currentDate,
    companyName: contractInvoiceData.service_provider?.name || 'Your Company',
    companyEmail: contractInvoiceData.service_provider?.email,
    tax: taxAmount,
    total: finalTotal
  };
}

export function createInvoiceFromContractData(
  contractInvoiceData: ContractInvoiceData,
  contractName: string
): AdaptedInvoiceData[] {
  if (!contractInvoiceData) {
    return [];
  }
  
  return [adaptContractInvoiceData(contractInvoiceData, contractName)];
}