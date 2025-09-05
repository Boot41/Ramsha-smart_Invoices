export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    CHANGE_PASSWORD: '/auth/change-password',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
    PROFILE: '/auth/profile',
    VERIFY_EMAIL: '/auth/verify-email',
    ME: '/auth/me',
  },
  DOCUMENTS: {
    BASE: '/documents',
    UPLOAD: '/documents/upload',
    BULK_UPLOAD: '/documents/upload/bulk',
    UPLOAD_LEGACY: '/documents/upload-contract', // Legacy endpoint
  },
  CONTRACTS: {
    BASE: '/contracts',
  GET_CONTRACTS:(userId: string) => `/contracts/user/${userId}`,
    UPLOAD_AND_PROCESS: '/contracts/upload-and-process',
    GENERATE_INVOICE_DATA: '/contracts/generate-invoice-data',
    QUERY: '/contracts/query',
    PROCESS_AND_GENERATE_INVOICE: '/contracts/process-and-generate-invoice',
    GET_DOWNLOAD_URL: (userId: string, contractPath: string) => `/contracts/download/${userId}/${encodeURIComponent(contractPath)}`,
    HEALTH: '/contracts/health',
  },
  ORCHESTRATOR: {
    START_INVOICE_WORKFLOW: '/api/v1/adk/workflow/invoice/start',
    START_AGENTIC_WORKFLOW: '/api/v1/adk/workflow/invoice/start-for-contract',
  },
  MCP: {
    SYNC_CONTRACTS: '/api/v1/mcp/gdrive/contracts',
    SYNC_RENTAL_CONTRACTS: '/api/v1/mcp/gdrive/rental-contracts',
    WEBHOOK: '/api/v1/mcp/gdrive/webhook',
  }
  // Add other API endpoints as needed
};

export const TOKEN_STORAGE_KEY = 'authToken';