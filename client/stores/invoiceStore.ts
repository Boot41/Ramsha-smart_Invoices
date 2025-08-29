import { create } from 'zustand';
import type { ContractProcessResponse, InvoiceGenerationResponse } from '../api/contracts';

interface InvoiceStoreState {
  [x: string]: any;
  contractProcessing: ContractProcessResponse | null;
  invoiceGeneration: InvoiceGenerationResponse | null;
  setContractProcessing: (data: ContractProcessResponse) => void;
  setInvoiceGeneration: (data: InvoiceGenerationResponse) => void;
  reset: () => void;
}

export const useInvoiceStore = create<InvoiceStoreState>((set) => ({
  contractProcessing: null,
  invoiceGeneration: null,
  setContractProcessing: (data) => set({ contractProcessing: data }),
  setInvoiceGeneration: (data) => set({ invoiceGeneration: data }),
  reset: () => set({ contractProcessing: null, invoiceGeneration: null }),
}));
