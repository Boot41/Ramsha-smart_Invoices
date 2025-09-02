import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { contractsApi } from '../api/contracts';
import type { 
  ContractInfo, 
  ContractListResponse, 
  ContractProcessResponse,
  ContractDownloadResponse,
  InvoiceGenerationResponse
} from '../api/contracts';

interface ContractState {
  contracts: ContractInfo[];
  isLoading: boolean;
  error: string | null;
  uploadProgress: number;
  selectedContract: ContractInfo | null;
  lastProcessedContract: ContractProcessResponse | null;
  lastGeneratedInvoice: InvoiceGenerationResponse | null;
}

interface ContractActions {
  // Contract listing
  fetchContracts: (userId: string) => Promise<void>;
  
  // Contract upload and processing
  uploadAndProcessContract: (file: File, userId: string) => Promise<ContractProcessResponse>;
  
  // Contract download
  getDownloadUrl: (userId: string, contractPath: string, expiresInHours?: number) => Promise<string>;
  
  // Invoice generation
  generateInvoiceData: (userId: string, contractName: string, query?: string) => Promise<InvoiceGenerationResponse>;
  
  // Complete workflow
  processAndGenerateInvoice: (file: File, userId: string) => Promise<any>;
  
  // Contract selection
  selectContract: (contract: ContractInfo | null) => void;
  
  // State management
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;
  
  // Progress tracking
  setUploadProgress: (progress: number) => void;
}

type ContractStore = ContractState & ContractActions;

export const useContractStore = create<ContractStore>()(
  persist(
    (set, get) => ({
      // Initial state
      contracts: [],
      isLoading: false,
      error: null,
      uploadProgress: 0,
      selectedContract: null,
      lastProcessedContract: null,
      lastGeneratedInvoice: null,

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
          } catch (error: any) {
            console.error('Failed to fetch contracts:', error);
            set({ 
              error: error.message || 'Failed to fetch contracts',
              isLoading: false 
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

      selectContract: (contract: ContractInfo | null) => {
        set({ selectedContract: contract });
      },

      setLoading: (loading: boolean) => set({ isLoading: loading }),
      
      setError: (error: string | null) => set({ error }),
      
      clearError: () => set({ error: null }),
      
      setUploadProgress: (progress: number) => set({ uploadProgress: progress }),

      reset: () => set({ 
        contracts: [],
        isLoading: false,
        error: null,
        uploadProgress: 0,
        selectedContract: null,
        lastProcessedContract: null,
        lastGeneratedInvoice: null
      })
    }),
    {
      name: 'contract-store',
      partialize: (state) => ({
        contracts: state.contracts,
        selectedContract: state.selectedContract,
        lastProcessedContract: state.lastProcessedContract,
        lastGeneratedInvoice: state.lastGeneratedInvoice
      })
    }
  )
);