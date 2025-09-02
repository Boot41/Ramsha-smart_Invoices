import { apiClient } from './base';
import { API_ENDPOINTS } from './config';

export interface ContractProcessResponse {
  status: string;
  message: string;
  contract_name: string;
  user_id: string;
  total_chunks: number;
  total_embeddings: number;
  vector_ids: string[];
  text_preview: string;
  processing_timestamp: string;
}

export interface InvoiceGenerationRequest {
  user_id: string;
  contract_name: string;
  query?: string;
  specific_requirements?: string[];
}

export interface ContractInvoiceData {
  contract_title?: string;
  contract_type?: string;
  contract_number?: string;
  client?: {
    name: string;
    email?: string;
    address?: string;
    phone?: string;
    tax_id?: string;
    role: string;
  };
  service_provider?: {
    name: string;
    email?: string;
    address?: string;
    phone?: string;
    tax_id?: string;
    role: string;
  };
  start_date?: string;
  end_date?: string;
  effective_date?: string;
  payment_terms?: {
    amount?: number;
    currency?: string;
    frequency?: string;
    due_days?: number;
    late_fee?: number;
    discount_terms?: string;
  };
  services?: {
    description: string;
    quantity?: number;
    unit_price?: number;
    total_amount?: number;
    unit?: string;
  }[];
  invoice_frequency?: string;
  first_invoice_date?: string;
  next_invoice_date?: string;
  special_terms?: string;
  notes?: string;
  confidence_score?: number;
  extracted_at?: string;
}

export interface InvoiceGenerationResponse {
  status: string;
  message: string;
  contract_name: string;
  user_id: string;
  invoice_data: ContractInvoiceData;
  raw_response?: string;
  confidence_score?: number;
  generated_at: string;
}

export interface ContractQueryRequest {
  user_id: string;
  contract_name: string;
  query: string;
}

export interface ContractQueryResponse {
  status: string;
  response: string;
  contract_name: string;
  user_id: string;
  query: string;
  generated_at: string;
}


export interface StartWorkflowResponse {
  workflow_id: string;
  status: string;
  message: string;
  received_at: string;
}

export class ContractsApi {
  /**
   * Upload and process a contract PDF file
   */
  static async uploadAndProcessContract(
    file: File,
    userId: string
  ): Promise<ContractProcessResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    return apiClient.post<ContractProcessResponse>(
      API_ENDPOINTS.CONTRACTS.UPLOAD_AND_PROCESS,
      formData,
      { isMultipart: true }
    );
  }

  /**
   * Generate structured invoice data from a processed contract
   */
  static async generateInvoiceData(
    request: InvoiceGenerationRequest
  ): Promise<InvoiceGenerationResponse> {
    return apiClient.post<InvoiceGenerationResponse>(
      API_ENDPOINTS.CONTRACTS.GENERATE_INVOICE_DATA,
      request
    );
  }

  /**
   * Query a processed contract for specific information
   */
  static async queryContract(
    request: ContractQueryRequest
  ): Promise<ContractQueryResponse> {
    return apiClient.post<ContractQueryResponse>(
      API_ENDPOINTS.CONTRACTS.QUERY,
      request
    );
  }

  /**
   * Complete workflow: Upload contract, process it, and generate invoice data
   */
  static async processAndGenerateInvoice(
    file: File,
    userId: string
  ): Promise<{
    status: string;
    message: string;
    contract_processing: ContractProcessResponse;
    invoice_generation: InvoiceGenerationResponse;
    workflow_completed_at: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    return apiClient.post(
      API_ENDPOINTS.CONTRACTS.PROCESS_AND_GENERATE_INVOICE,
      formData,
      { isMultipart: true }
    );
  }

  /**
   * Start a new agentic invoice processing workflow
   */
  static async startInvoiceWorkflow(
    file: File,
    userId: string,
    contractName: string
  ): Promise<StartWorkflowResponse> {
    const formData = new FormData();
    formData.append('contract_file', file);
    formData.append('user_id', userId);
    formData.append('contract_name', contractName);

    return apiClient.post<StartWorkflowResponse>(
      API_ENDPOINTS.ORCHESTRATOR.START_INVOICE_WORKFLOW,
      formData,
      { isMultipart: true }
    );
  }

  /**
   * Check health status of contract processing service
   */
  static async healthCheck(): Promise<{
    status: string;
    message: string;
    services: Record<string, string>;
    timestamp: string;
  }> {
    return apiClient.get(API_ENDPOINTS.CONTRACTS.HEALTH, {
      requiresAuth: false,
    });
  }
}

// ✅ Export instance methods (like authApi)
export const contractsApi = {
  uploadAndProcessContract: ContractsApi.uploadAndProcessContract.bind(ContractsApi),
  generateInvoiceData: ContractsApi.generateInvoiceData.bind(ContractsApi),
  queryContract: ContractsApi.queryContract.bind(ContractsApi),
  processAndGenerateInvoice: ContractsApi.processAndGenerateInvoice.bind(ContractsApi),
  startInvoiceWorkflow: ContractsApi.startInvoiceWorkflow.bind(ContractsApi),
  healthCheck: ContractsApi.healthCheck.bind(ContractsApi),
};
