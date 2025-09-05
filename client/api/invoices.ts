import { apiClient } from './base';

export interface Invoice {
  id: string;
  invoice_number: string;
  workflow_id: string;
  user_id?: string;
  
  // Invoice details
  invoice_date: string;
  due_date: string;
  status: 'draft' | 'generated' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  
  // Parties information
  client_name: string;
  client_email?: string;
  client_address?: string;
  client_phone?: string;
  
  service_provider_name: string;
  service_provider_email?: string;
  service_provider_address?: string;
  service_provider_phone?: string;
  
  // Financial information
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  currency: string;
  
  // Contract details
  contract_title?: string;
  contract_type?: string;
  contract_reference?: string;
  
  // Complete invoice data (JSON)
  invoice_data: any;
  
  // AI generation metadata
  generated_by_agent: string;
  confidence_score?: number;
  quality_score?: number;
  human_reviewed: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
  page: number;
  per_page: number;
}

export const invoicesAPI = {
  // Get all invoices for a user
  getInvoices: async (
    userId: string,
    page = 1,
    perPage = 10,
    status?: string
  ): Promise<InvoiceListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    if (status) {
      params.append('status', status);
    }
    
    const response = await api.get(`/invoices/user/${userId}?${params}`);
    return response.data;
  },

  // Get a specific invoice by ID
  getInvoice: async (invoiceId: string): Promise<Invoice> => {
    const response = await api.get(`/invoices/${invoiceId}`);
    return response.data;
  },

  // Get invoice by workflow ID
  getInvoiceByWorkflow: async (workflowId: string): Promise<Invoice> => {
    const response = await api.get(`/invoices/workflow/${workflowId}`);
    return response.data;
  },

  // Update invoice status
  updateInvoiceStatus: async (
    invoiceId: string,
    status: Invoice['status']
  ): Promise<Invoice> => {
    const response = await api.patch(`/invoices/${invoiceId}/status`, { status });
    return response.data;
  },

  // Download invoice as PDF
  downloadInvoice: async (invoiceId: string): Promise<Blob> => {
    const response = await api.get(`/invoices/${invoiceId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Send invoice by email
  sendInvoice: async (
    invoiceId: string,
    recipientEmail?: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/invoices/${invoiceId}/send`, {
      recipient_email: recipientEmail
    });
    return response.data;
  }
};

export default invoicesAPI;