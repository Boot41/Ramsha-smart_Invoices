/**
 * Invoice Scheduler API Service
 * 
 * Handles all API calls related to invoice scheduling and schedule extraction
 */

export interface ScheduleExtractRequest {
  user_id?: string;
}

export interface ScheduleDetails {
  extraction_method: string;
  contract_id: string;
  found_schedule_info: boolean;
  number_of_invoices: number | null;
  frequency: string | null;
  send_dates: string[];
  confidence_score: number;
  payment_due_days?: number;
  analysis_summary?: string;
  raw_matches?: Array<{
    score: number;
    metadata: any;
    text_preview: string;
  }>;
}

export interface ExtractedSchedule {
  invoice_id: string;
  invoice_number: string;
  workflow_id: string;
  contract_id: string;
  contract_reference: string | null;
  client_name: string;
  client_email: string | null;
  total_amount: number;
  currency: string;
  invoice_date: string | null;
  due_date: string | null;
  status: string;
  schedule_details: ScheduleDetails;
}

export interface ScheduleExtractionResponse {
  success: boolean;
  message: string;
  total_invoices: number;
  processed_invoices: number;
  schedule_extracts: ExtractedSchedule[];
  extraction_timestamp: string;
  error?: string;
}

export interface InvoiceSchedulerStatus {
  invoice_scheduler_agent: {
    agent_name: string;
    status: string;
    services: {
      pinecone: string;
      gemini_ai: string;
      gmail_mcp: string;
    };
    capabilities: string[];
    pinecone_stats: any;
    timestamp: string;
  };
  cloud_scheduler: any;
  gmail_mcp: any;
  overall_status: string;
  timestamp: string;
}

class InvoiceSchedulerAPI {
  private baseURL: string;

  constructor() {
    // Use Vite environment variables or fallback to localhost
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    console.log('🔗 Invoice Scheduler API initialized with base URL:', this.baseURL);
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      console.log(`📡 Making API request: ${config.method || 'GET'} ${url}`);
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.text();
        const errorMessage = `HTTP ${response.status}: ${errorData}`;
        console.error('❌ API request failed:', errorMessage);
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('✅ API request successful:', endpoint, data);
      return data;
    } catch (error) {
      console.error('❌ API request failed:', { endpoint, error });
      throw error;
    }
  }

  /**
   * Extract schedules from database invoices using RAG
   */
  async extractSchedules(request: ScheduleExtractRequest = {}): Promise<ScheduleExtractionResponse> {
    return this.request<ScheduleExtractionResponse>(
      '/invoice-scheduler/schedules/extract',
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  /**
   * Get invoice scheduler status
   */
  async getStatus(): Promise<InvoiceSchedulerStatus> {
    return this.request<InvoiceSchedulerStatus>('/invoice-scheduler/status');
  }

  /**
   * Search for invoice schedules using natural language query
   */
  async searchSchedules(query: string, topK: number = 10): Promise<any> {
    return this.request(
      `/invoice-scheduler/schedules/search?query=${encodeURIComponent(query)}&top_k=${topK}`
    );
  }

  /**
   * Get schedules by specific date
   */
  async getSchedulesByDate(date: string): Promise<any> {
    return this.request(`/invoice-scheduler/schedules/date/${date}`);
  }

  /**
   * Create sample schedules for testing
   */
  async createSampleSchedules(): Promise<any> {
    return this.request('/invoice-scheduler/schedules/create-samples', {
      method: 'POST',
    });
  }
}

export const invoiceSchedulerAPI = new InvoiceSchedulerAPI();