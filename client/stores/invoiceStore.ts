import { create } from 'zustand';
import type { ContractProcessResponse, InvoiceGenerationResponse } from '../api/contracts';

interface UIInvoiceComponent {
  component_name: string;
  file_path: string;
  component_type: string;
  generated_at: string;
  model_used: string;
}

interface InvoiceStoreState {
  [x: string]: any;
  contractProcessing: ContractProcessResponse | null;
  invoiceGeneration: InvoiceGenerationResponse | null;
  workflowId: string | null;
  uiInvoiceComponent: UIInvoiceComponent | null;
  setContractProcessing: (data: ContractProcessResponse) => void;
  setInvoiceGeneration: (data: InvoiceGenerationResponse) => void;
  setWorkflowId: (id: string) => void;
  setUiInvoiceComponent: (data: UIInvoiceComponent) => void;
  reset: () => void;
}

export const useInvoiceStore = create<InvoiceStoreState>((set) => ({
  contractProcessing: null,
  invoiceGeneration: null,
  workflowId: null,
  uiInvoiceComponent: null,
  setContractProcessing: (data) => set({ contractProcessing: data }),
  setInvoiceGeneration: (data) => set({ invoiceGeneration: data }),
  setWorkflowId: (id) => set({ workflowId: id }),
  setUiInvoiceComponent: (data) => set({ uiInvoiceComponent: data }),
  reset: () => set({ contractProcessing: null, invoiceGeneration: null, workflowId: null, uiInvoiceComponent: null }),
}));
