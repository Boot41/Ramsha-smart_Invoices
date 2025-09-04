// API service for making HTTP requests to the backend
const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface InvoiceDesign {
  design_name: string;
  design_id: string;
  style_theme: string;
  components: InvoiceComponent[];
}

export interface InvoiceComponent {
  type: string;
  props: Record<string, any>;
  styling: Record<string, any>;
}

export interface AdaptiveUIDesignsResponse {
  invoice_id: string;
  invoice_number?: string;
  workflow_id?: string;
  client_name?: string;
  service_provider_name?: string;
  designs: InvoiceDesign[];
  generated_at?: string;
  total_designs: number;
  message?: string;
}

export class ApiService {
  private static baseURL = API_BASE_URL;

  private static async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Get adaptive UI designs for an invoice
  static async getInvoiceDesigns(invoiceId: string): Promise<AdaptiveUIDesignsResponse> {
    return this.makeRequest<AdaptiveUIDesignsResponse>(
      `/invoices/${invoiceId}/adaptive-ui-designs`
    );
  }

  // Get invoice details
  static async getInvoice(invoiceId: string): Promise<any> {
    return this.makeRequest(`/invoices/database/${invoiceId}`);
  }

  // List all invoices
  static async getInvoices(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    
    const queryString = queryParams.toString();
    const endpoint = `/invoices/database/list${queryString ? `?${queryString}` : ''}`;
    
    return this.makeRequest(endpoint);
  }
}

export default ApiService;