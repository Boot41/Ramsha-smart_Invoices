export enum DocumentType {
  CONTRACT = "contract",
  INVOICE = "invoice",
  RECEIPT = "receipt",
  OTHER = "other",
}

export enum UploadSource {
  WEB_UPLOAD = "web_upload",
  EMAIL = "email",
  DRIVE = "drive",
}

export interface DocumentUploadRequest {
  filename: string;
  document_type: DocumentType;
  description?: string;
  tags?: string[];
  source: UploadSource;
  metadata?: Record<string, any>;
}

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  document_id?: string;
  filename?: string;
  document_type?: DocumentType;
  timestamp?: string;
}

export interface BulkDocumentUploadRequest {
  documents: DocumentUploadRequest[];
  batch_metadata?: Record<string, any>;
}

export interface BulkDocumentUploadResponse {
  successful_uploads: number;
  failed_uploads: number;
  total_documents: number;
  results: { success: boolean; document_id?: string; filename: string; message: string }[];
  message: string;
}

export interface DocumentResponse {
  id: string;
  filename: string;
  document_type: DocumentType;
  description?: string;
  tags?: string[];
  source: UploadSource;
  metadata?: Record<string, any>;
  uploaded_at: string;
  owner_id: string;
  status: string;
}

export interface DocumentProcessingResponse {
  success: boolean;
  message: string;
  document_id: string;
  processing_status: string;
  timestamp: string;
}

export interface ListDocumentsResponse {
  success: boolean;
  message: string;
  documents: DocumentResponse[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
