import React from 'react';

// Create a registry of available invoice components
const componentRegistry: Record<string, () => Promise<any>> = {
  'invoice-d88c29ed': () => import('../components/invoices/invoice-d88c29ed'),
  'invoice-183d5e13': () => import('../components/invoices/invoice-183d5e13'),
  'invoice-210ebede': () => import('../components/invoices/invoice-210ebede'),
  'invoice-component-210ebede': () => import('../components/invoices/invoice-component-210ebede'),
};

export interface ComponentLoaderResult {
  component: React.ComponentType<any> | null;
  loading: boolean;
  error: string | null;
}

export async function loadInvoiceComponent(templateId: string): Promise<React.ComponentType<any> | null> {
  try {
    const loader = componentRegistry[templateId];
    if (!loader) {
      console.warn(`No component loader found for template: ${templateId}`);
      return null;
    }

    const module = await loader();
    return module.default || module;
  } catch (error) {
    console.error(`Failed to load component ${templateId}:`, error);
    return null;
  }
}

// Sample invoice data for preview
export const createSampleInvoiceData = (templateId: string) => {
  const amount = Math.floor(Math.random() * 5000) + 1000;
  
  return {
    contract_title: "Professional Services Agreement",
    contract_type: "Service Agreement", 
    contract_number: `DEMO-${templateId.slice(-4)}`,
    client: {
      name: "Demo Client Inc.",
      email: "demo@client.com",
      address: "123 Business Ave, Corporate City, CC 12345",
      phone: "+1 (555) 123-4567",
      tax_id: "12-3456789",
      role: "Client"
    },
    service_provider: {
      name: "Your Company Name",
      email: "info@yourcompany.com", 
      address: "456 Service St, Provider City, PC 67890",
      phone: "+1 (555) 987-6543",
      tax_id: "98-7654321",
      role: "Service Provider"
    },
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    effective_date: "2024-01-01",
    payment_terms: {
      amount: amount,
      currency: "$",
      frequency: "monthly",
      due_days: 30,
      late_fee: 50,
      discount_terms: "2/10 net 30"
    },
    services: [
      {
        description: "Consulting Services",
        quantity: 10,
        unit_price: 150,
        total_amount: 1500,
        unit: "hours"
      },
      {
        description: "Implementation Services", 
        quantity: 20,
        unit_price: 120,
        total_amount: 2400,
        unit: "hours"
      }
    ],
    invoice_frequency: "monthly",
    first_invoice_date: "2024-02-01",
    next_invoice_date: "2024-03-01",
    special_terms: "Payment due within 30 days of invoice date",
    notes: "This is a preview of the invoice template using sample data.",
    confidence_score: 0.95,
    extracted_at: new Date().toISOString()
  };
};

// Create props for different component types
export const createComponentProps = (templateId: string, invoiceData: any, invoiceNumber: string, invoiceDate: Date, dueDate: Date, status: string) => {
  // For components that expect individual props (like invoice-210ebede)
  if (templateId.includes('210ebede') || templateId.includes('component')) {
    return {
      serviceProvider: invoiceData.service_provider?.name || "Your Company Name",
      clientName: invoiceData.client?.name || "Demo Client Inc.",
      service: invoiceData.contract_title || "Professional Services",
      amount: invoiceData.payment_terms?.amount || 1500,
      billingFrequency: invoiceData.payment_terms?.frequency || "monthly",
      invoiceData: invoiceData,
      invoiceNumber,
      invoiceDate,
      dueDate,
      status
    };
  }
  
  // For components that expect structured invoiceData (like invoice-d88c29ed)
  return {
    invoiceData: invoiceData,
    invoiceNumber,
    invoiceDate,
    dueDate,
    status
  };
};