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

export interface MCPContract {
  file_id: string;
  name: string;
  mime_type: string;
  gdrive_uri: string;
  processing_result?: ContractProcessResponse;
  processed: boolean;
  processing_error?: string;
  source: 'mcp';
}

export interface MCPSyncResponse {
  status: string;
  message: string;
  contracts: MCPContract[];
  total_count: number;
  processed_count: number;
  sync_only: boolean;
  processing_note?: string;
  mcp_benefits_used: string[];
}

export interface MCPRentalContract extends MCPContract {
  contract_type: 'rental_lease';
}

export interface MCPRentalSyncResponse extends MCPSyncResponse {
  contracts: MCPRentalContract[];
  contract_type_focus: 'rental_lease';
  rental_specific_features: string[];
}


export interface StartWorkflowResponse {
  workflow_id: string;
  status: string;
  message: string;
  received_at: string;
}

export interface ContractDownloadResponse {
  download_url: string;
  expires_at: string;
}

export interface StartAgenticWorkflowRequest {
  user_id: string;
  contract_name: string;
  contract_path?: string;
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
   * Start agentic workflow for an existing contract
   */
  static async startAgenticWorkflow(
    request: StartAgenticWorkflowRequest
  ): Promise<StartWorkflowResponse> {
    const formData = new FormData();
    formData.append('user_id', request.user_id);
    formData.append('contract_name', request.contract_name);
    formData.append('max_attempts', '3');
    formData.append('options', JSON.stringify({ 
      existing_contract: true, 
      contract_path: request.contract_path 
    }));
    
    // Create a dummy file to indicate existing contract
    const dummyFile = new Blob([''], { type: 'application/pdf' });
    formData.append('contract_file', dummyFile, 'existing_contract.pdf');

    return apiClient.post<StartWorkflowResponse>(
      API_ENDPOINTS.ORCHESTRATOR.START_INVOICE_WORKFLOW,
      formData,
      { isMultipart: true }
    );
  }

  /**
   * Get download URL for a contract
   */
  static async getContractDownloadUrl(
    userId: string,
    contractPath: string,
    expiresInHours: number = 1
  ): Promise<ContractDownloadResponse> {
    return apiClient.get<ContractDownloadResponse>(
      API_ENDPOINTS.CONTRACTS.GET_DOWNLOAD_URL(userId, contractPath) + `?expires_in_hours=${expiresInHours}`
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

    /**
     * Get contracts for a specific user
     */
    static async getContracts(userId: string): Promise<any> {
      return apiClient.get(API_ENDPOINTS.CONTRACTS.GET_CONTRACTS(userId));
    }

  /**
   * Sync contracts from Google Drive using MCP (sync only by default)
   */
  static async syncMCPContracts(
    userId?: string,
    query?: string,
    processFiles = false
  ): Promise<MCPSyncResponse> {
    const params = new URLSearchParams({
      process_files: processFiles.toString(),
    });
    
    if (userId) {
      params.append('user_id', userId);
    }
    
    if (query) {
      params.append('query', query);
    }

    return apiClient.get<MCPSyncResponse>(
      `${API_ENDPOINTS.MCP.SYNC_CONTRACTS}?${params.toString()}`
    );
  }

  /**
   * Sync rental contracts specifically from Google Drive using MCP (sync only by default)
   */
  static async syncMCPRentalContracts(
    userId?: string,
    query?: string,
    processFiles = false
  ): Promise<MCPRentalSyncResponse> {
    const params = new URLSearchParams({
      process_files: processFiles.toString(),
    });
    
    if (userId) {
      params.append('user_id', userId);
    }
    
    if (query) {
      params.append('query', query);
    }

    return apiClient.get<MCPRentalSyncResponse>(
      `${API_ENDPOINTS.MCP.SYNC_RENTAL_CONTRACTS}?${params.toString()}`
    );
  }
}

// ✅ Export instance methods (like authApi)
export const contractsApi = {
  uploadAndProcessContract: ContractsApi.uploadAndProcessContract.bind(ContractsApi),
  generateInvoiceData: ContractsApi.generateInvoiceData.bind(ContractsApi),
  queryContract: ContractsApi.queryContract.bind(ContractsApi),
  processAndGenerateInvoice: ContractsApi.processAndGenerateInvoice.bind(ContractsApi),
  startInvoiceWorkflow: ContractsApi.startInvoiceWorkflow.bind(ContractsApi),
  startAgenticWorkflow: ContractsApi.startAgenticWorkflow.bind(ContractsApi),
  getContractDownloadUrl: ContractsApi.getContractDownloadUrl.bind(ContractsApi),
  healthCheck: ContractsApi.healthCheck.bind(ContractsApi),
  getContracts: ContractsApi.getContracts.bind(ContractsApi),
  syncMCPContracts: ContractsApi.syncMCPContracts.bind(ContractsApi),
  syncMCPRentalContracts: ContractsApi.syncMCPRentalContracts.bind(ContractsApi),
};
