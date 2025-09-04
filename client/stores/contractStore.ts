import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { contractsApi } from '../api/contracts';
import type { 
  ContractInfo, 
  ContractListResponse, 
  ContractProcessResponse,
  ContractDownloadResponse,
  InvoiceGenerationResponse,
  MCPContract,
  MCPSyncResponse,
  MCPRentalContract,
  MCPRentalSyncResponse
} from '../api/contracts';

interface ContractState {
  contracts: ContractInfo[];
  mcpContracts: MCPContract[];
  mcpRentalContracts: MCPRentalContract[];
  allContracts: (ContractInfo & { source: 'manual' } | MCPContract & { source: 'mcp' })[];
  isLoading: boolean;
  isSyncingMCP: boolean;
  isSyncingRentals: boolean;
  error: string | null;
  mcpError: string | null;
  rentalError: string | null;
  uploadProgress: number;
  selectedContract: ContractInfo | null;
  lastProcessedContract: ContractProcessResponse | null;
  lastGeneratedInvoice: InvoiceGenerationResponse | null;
  lastMCPSync: MCPSyncResponse | null;
  lastRentalSync: MCPRentalSyncResponse | null;
}

interface ContractActions {
  // Contract listing
  fetchContracts: (userId: string) => Promise<void>;
  
  // MCP Contract syncing (sync-only by default)
  syncMCPContracts: (userId?: string, query?: string, processFiles?: boolean) => Promise<MCPSyncResponse>;
  syncMCPRentalContracts: (userId?: string, query?: string, processFiles?: boolean) => Promise<MCPRentalSyncResponse>;
  
  // Contract upload and processing
  uploadAndProcessContract: (file: File, userId: string) => Promise<ContractProcessResponse>;
  
  // Contract download
  getDownloadUrl: (userId: string, contractPath: string, expiresInHours?: number) => Promise<string>;
  
  // Invoice generation
  generateInvoiceData: (userId: string, contractName: string, query?: string) => Promise<InvoiceGenerationResponse>;
  
  // Complete workflow
  processAndGenerateInvoice: (file: File, userId: string) => Promise<any>;
  
  // Agentic workflow for existing contracts
  startAgenticWorkflow: (userId: string, contractName: string, contractPath?: string) => Promise<any>;
  
  // Contract selection
  selectContract: (contract: ContractInfo | null) => void;
  
  // State management
  setLoading: (loading: boolean) => void;
  setSyncingMCP: (syncing: boolean) => void;
  setSyncingRentals: (syncing: boolean) => void;
  setError: (error: string | null) => void;
  setMCPError: (error: string | null) => void;
  setRentalError: (error: string | null) => void;
  clearError: () => void;
  clearMCPError: () => void;
  clearRentalError: () => void;
  reset: () => void;
  
  // Progress tracking
  setUploadProgress: (progress: number) => void;
  
  // Combined data
  refreshAllContracts: () => void;
}

type ContractStore = ContractState & ContractActions;

export const useContractStore = create<ContractStore>()(
  persist(
    (set, get) => ({
      // Initial state
      contracts: [],
      mcpContracts: [],
      mcpRentalContracts: [],
      allContracts: [],
      isLoading: false,
      isSyncingMCP: false,
      isSyncingRentals: false,
      error: null,
      mcpError: null,
      rentalError: null,
      uploadProgress: 0,
      selectedContract: null,
      lastProcessedContract: null,
      lastGeneratedInvoice: null,
      lastMCPSync: null,
      lastRentalSync: null,

      // Actions
      fetchContracts: async (userId: string) => {
          console.log('contractStore.fetchContracts called with userId:', userId);
          set({ isLoading: true, error: null });
          try {
            console.log('Making API call to getContracts...');
            const response = await contractsApi.getContracts(userId);
            console.log('API response received:', response);
            // If response is an array, set directly; otherwise, try response.contracts
            let contractsRaw = Array.isArray(response) ? response : response.contracts || [];
            // Map and clean contracts
            const contracts = contractsRaw.map((contract: any) => {
              const mapped: any = {};
              // Map only non-empty fields
              Object.entries(contract).forEach(([key, value]) => {
                if (value !== null && value !== undefined && value !== '') {
                  mapped[key] = value;
                }
              });
              return mapped;
            });
            set({ 
              contracts,
              isLoading: false,
              error: null 
            });
            get().refreshAllContracts();
          } catch (error: any) {
            console.error('Failed to fetch contracts:', error);
            set({ 
              error: error.message || 'Failed to fetch contracts',
              isLoading: false 
            });
            throw error;
          }
      },

      syncMCPContracts: async (userId?: string, query?: string, processFiles = false) => {
        console.log('contractStore.syncMCPContracts called with userId:', userId);
        set({ isSyncingMCP: true, mcpError: null });
        try {
          const response = await contractsApi.syncMCPContracts(userId, query, processFiles);
          console.log('MCP sync response received:', response);
          
          // Add source tag to MCP contracts
          const mcpContracts = response.contracts.map(contract => ({
            ...contract,
            source: 'mcp' as const
          }));
          
          set({ 
            mcpContracts,
            lastMCPSync: response,
            isSyncingMCP: false,
            mcpError: null 
          });
          get().refreshAllContracts();
          
          return response;
        } catch (error: any) {
          console.error('Failed to sync MCP contracts:', error);
          console.log('🔍 Error structure debug:', {
            hasResponse: !!error.response,
            status: error.response?.status,
            data: error.response?.data,
            dataType: typeof error.response?.data,
            errorType: typeof error.response?.data?.error,
            directError: error.response?.data?.error,
            detailError: error.response?.data?.detail?.error,
            detailObject: error.response?.data?.detail,
            detailType: typeof error.response?.data?.detail,
            fullDataString: JSON.stringify(error.response?.data),
            fullError: error
          });
          
          // Handle OAuth token expiration - check multiple possible error structures
          const errorData = error.response?.data;
          const isOAuthExpired = error.response?.status === 401 && (
            errorData?.error === 'oauth_expired' ||
            errorData?.detail?.error === 'oauth_expired' ||
            (typeof errorData?.detail === 'object' && errorData?.detail?.error === 'oauth_expired')
          );
          
          console.log('🔐 OAuth expiration check:', {
            status401: error.response?.status === 401,
            directError: errorData?.error,
            detailError: errorData?.detail?.error,
            detailObjectError: (typeof errorData?.detail === 'object' && errorData?.detail?.error),
            finalResult: isOAuthExpired
          });
          
          if (isOAuthExpired) {
            console.log('🔑 OAuth token expired, redirecting to re-authenticate');
            console.log('🔄 About to redirect to: /auth/google-drive');
            set({ 
              isSyncingMCP: false,
              mcpError: 'Google Drive authentication expired. Please re-authenticate.'
            });
            
            // Redirect to Google Drive auth
            console.log('🚀 Executing redirect now...');
            window.location.href = '/auth/google-drive';
            console.log('✅ Redirect command executed');
            return;
          }
          
          set({ 
            mcpError: error.message || 'Failed to sync contracts from Google Drive',
            isSyncingMCP: false 
          });
          throw error;
        }
      },

      syncMCPRentalContracts: async (userId?: string, query?: string, processFiles = false) => {
        console.log('contractStore.syncMCPRentalContracts called with userId:', userId);
        set({ isSyncingRentals: true, rentalError: null });
        try {
          const response = await contractsApi.syncMCPRentalContracts(userId, query, processFiles);
          console.log('MCP rental sync response received:', response);
          
          // Add source tag to rental MCP contracts
          const mcpRentalContracts = response.contracts.map(contract => ({
            ...contract,
            source: 'mcp' as const
          }));
          
          set({ 
            mcpRentalContracts,
            lastRentalSync: response,
            isSyncingRentals: false,
            rentalError: null 
          });
          get().refreshAllContracts();
          
          return response;
        } catch (error: any) {
          console.error('Failed to sync MCP rental contracts:', error);
          
          // Handle OAuth token expiration - check multiple possible error structures
          const errorData = error.response?.data;
          const isOAuthExpired = error.response?.status === 401 && (
            errorData?.error === 'oauth_expired' ||
            errorData?.detail?.error === 'oauth_expired' ||
            (typeof errorData?.detail === 'object' && errorData?.detail?.error === 'oauth_expired')
          );
          
          if (isOAuthExpired) {
            console.log('🔑 OAuth token expired, redirecting to re-authenticate');
            set({ 
              isSyncingRentals: false,
              rentalError: 'Google Drive authentication expired. Please re-authenticate.'
            });
            
            // Redirect to Google Drive auth
            window.location.href = '/auth/google-drive';
            return;
          }
          
          set({ 
            rentalError: error.message || 'Failed to sync rental contracts from Google Drive',
            isSyncingRentals: false 
          });
          throw error;
        }
      },

      uploadAndProcessContract: async (file: File, userId: string) => {
        set({ isLoading: true, error: null, uploadProgress: 0 });
        try {
          // Simulate upload progress for better UX
          const progressInterval = setInterval(() => {
            set(state => ({ 
              uploadProgress: Math.min(state.uploadProgress + 10, 90) 
            }));
          }, 200);

          const response = await contractsApi.uploadAndProcessContract(file);
          
          clearInterval(progressInterval);
          set({ 
            lastProcessedContract: response,
            isLoading: false,
            uploadProgress: 100,
            error: null 
          });

          // Refresh contracts list
          setTimeout(() => {
            get().fetchContracts(userId);
            set({ uploadProgress: 0 });
          }, 1000);

          return response;
        } catch (error: any) {
          console.error('Failed to upload and process contract:', error);
          set({ 
            error: error.message || 'Failed to upload and process contract',
            isLoading: false,
            uploadProgress: 0
          });
          throw error;
        }
      },

      getDownloadUrl: async (userId: string, contractPath: string, expiresInHours = 1) => {
        set({ isLoading: true, error: null });
        try {
          const response = await contractsApi.getContractDownloadUrl(userId, contractPath, expiresInHours);
          set({ isLoading: false, error: null });
          return response.download_url;
        } catch (error: any) {
          console.error('Failed to get download URL:', error);
          set({ 
            error: error.message || 'Failed to get download URL',
            isLoading: false 
          });
          throw error;
        }
      },

      generateInvoiceData: async (userId: string, contractName: string, query?: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await contractsApi.generateInvoiceData({
            user_id: userId,
            contract_name: contractName,
            query: query || 'Extract comprehensive invoice data including all parties, payment terms, services, and billing schedules'
          });
          
          set({ 
            lastGeneratedInvoice: response,
            isLoading: false,
            error: null 
          });
          
          return response;
        } catch (error: any) {
          console.error('Failed to generate invoice data:', error);
          set({ 
            error: error.message || 'Failed to generate invoice data',
            isLoading: false 
          });
          throw error;
        }
      },

      processAndGenerateInvoice: async (file: File, userId: string) => {
        set({ isLoading: true, error: null, uploadProgress: 0 });
        try {
          // Simulate upload progress
          const progressInterval = setInterval(() => {
            set(state => ({ 
              uploadProgress: Math.min(state.uploadProgress + 8, 95) 
            }));
          }, 300);

          const response = await contractsApi.processAndGenerateInvoice(file);
          
          clearInterval(progressInterval);
          set({ 
            lastProcessedContract: response.contract_processing,
            lastGeneratedInvoice: response.invoice_generation,
            isLoading: false,
            uploadProgress: 100,
            error: null 
          });

          // Refresh contracts list after processing
          setTimeout(() => {
            get().fetchContracts(userId);
            set({ uploadProgress: 0 });
          }, 1000);

          return response;
        } catch (error: any) {
          console.error('Failed to process and generate invoice:', error);
          set({ 
            error: error.message || 'Failed to process and generate invoice',
            isLoading: false,
            uploadProgress: 0
          });
          throw error;
        }
      },

      startAgenticWorkflow: async (userId: string, contractName: string, contractPath?: string) => {
        set({ isLoading: true, error: null });
        try {
          console.log('Starting agentic workflow for contract:', contractName);
          
          const response = await contractsApi.startAgenticWorkflow({
            user_id: userId,
            contract_name: contractName,
            contract_path: contractPath
          });
          
          set({ 
            isLoading: false,
            error: null 
          });
          
          console.log('Agentic workflow started successfully:', response);
          return response;
        } catch (error: any) {
          console.error('Failed to start agentic workflow:', error);
          
          // Handle OAuth token expiration - check multiple possible error structures
          const errorData = error.response?.data;
          const isOAuthExpired = error.response?.status === 401 && (
            errorData?.error === 'oauth_expired' ||
            errorData?.detail?.error === 'oauth_expired' ||
            (typeof errorData?.detail === 'object' && errorData?.detail?.error === 'oauth_expired')
          );
          
          if (isOAuthExpired) {
            console.log('🔑 OAuth token expired during workflow, redirecting to re-authenticate');
            set({ 
              isLoading: false,
              error: 'Google Drive authentication expired. Please re-authenticate.'
            });
            
            // Redirect to Google Drive auth
            window.location.href = '/auth/google-drive';
            return;
          }
          
          set({ 
            error: error.message || 'Failed to start agentic workflow',
            isLoading: false 
          });
          throw error;
        }
      },

      selectContract: (contract: ContractInfo | null) => {
        set({ selectedContract: contract });
      },

      setLoading: (loading: boolean) => set({ isLoading: loading }),
      
      setSyncingMCP: (syncing: boolean) => set({ isSyncingMCP: syncing }),
      
      setSyncingRentals: (syncing: boolean) => set({ isSyncingRentals: syncing }),
      
      setError: (error: string | null) => set({ error }),
      
      setMCPError: (error: string | null) => set({ mcpError: error }),
      
      setRentalError: (error: string | null) => set({ rentalError: error }),
      
      clearError: () => set({ error: null }),
      
      clearMCPError: () => set({ mcpError: null }),
      
      clearRentalError: () => set({ rentalError: null }),
      
      setUploadProgress: (progress: number) => set({ uploadProgress: progress }),

      refreshAllContracts: () => {
        const { contracts, mcpContracts, mcpRentalContracts } = get();
        
        // Combine manual and MCP contracts
        const manualContracts = contracts.map(contract => ({
          ...contract,
          source: 'manual' as const
        }));
        
        const allContracts = [...manualContracts, ...mcpContracts, ...mcpRentalContracts];
        
        set({ allContracts });
      },

      reset: () => set({ 
        contracts: [],
        mcpContracts: [],
        mcpRentalContracts: [],
        allContracts: [],
        isLoading: false,
        isSyncingMCP: false,
        isSyncingRentals: false,
        error: null,
        mcpError: null,
        rentalError: null,
        uploadProgress: 0,
        selectedContract: null,
        lastProcessedContract: null,
        lastGeneratedInvoice: null,
        lastMCPSync: null,
        lastRentalSync: null
      })
    }),
    {
      name: 'contract-store',
      partialize: (state) => ({
        contracts: state.contracts,
        mcpContracts: state.mcpContracts,
        mcpRentalContracts: state.mcpRentalContracts,
        allContracts: state.allContracts,
        selectedContract: state.selectedContract,
        lastProcessedContract: state.lastProcessedContract,
        lastGeneratedInvoice: state.lastGeneratedInvoice,
        lastMCPSync: state.lastMCPSync,
        lastRentalSync: state.lastRentalSync
      })
    }
  )
);