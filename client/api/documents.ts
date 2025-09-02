import { apiClient } from './base';
import { API_ENDPOINTS } from './config';
import {
  DocumentUploadRequest,
  DocumentUploadResponse,
  BulkDocumentUploadRequest,
  BulkDocumentUploadResponse,
  DocumentResponse,
  DocumentProcessingResponse,
  ListDocumentsResponse,
  DocumentType,
  UploadSource,
} from '../types'; // Assuming types are in ../types/index.ts

export class DocumentsApi {
  static async uploadDocument(
    file: File,
    filename: string,
    document_type: DocumentType,
    description?: string,
    tags?: string[],
    source: UploadSource = UploadSource.WEB_UPLOAD,
    metadata?: Record<string, any>
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('filename', filename);
    formData.append('document_type', document_type);
    if (description) formData.append('description', description);
    if (tags) formData.append('tags', JSON.stringify(tags));
    formData.append('source', source);
    if (metadata) formData.append('metadata', JSON.stringify(metadata));

    return apiClient.post<DocumentUploadResponse>(
      API_ENDPOINTS.DOCUMENTS.UPLOAD,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  }

  static async bulkUploadDocuments(
    files: File[],
    documents: DocumentUploadRequest[],
    batch_metadata?: Record<string, any>
  ): Promise<BulkDocumentUploadResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('documents_json', JSON.stringify(documents));
    if (batch_metadata) formData.append('batch_metadata', JSON.stringify(batch_metadata));

    return apiClient.post<BulkDocumentUploadResponse>(
      API_ENDPOINTS.DOCUMENTS.BULK_UPLOAD,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  }

  static async getDocument(documentId: string): Promise<DocumentResponse> {
    return apiClient.get<DocumentResponse>(
      `${API_ENDPOINTS.DOCUMENTS.BASE}/${documentId}`
    );
  }

  static async deleteDocument(documentId: string): Promise<{ success: boolean; message: string; document_id: string }> {
    return apiClient.delete<{ success: boolean; message: string; document_id: string }>(
      `${API_ENDPOINTS.DOCUMENTS.BASE}/${documentId}`
    );
  }

  static async listDocuments(
    document_type?: DocumentType,
    limit: number = 50,
    offset: number = 0
  ): Promise<ListDocumentsResponse> {
    const params = new URLSearchParams();
    if (document_type) params.append('document_type', document_type);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    return apiClient.get<ListDocumentsResponse>(
      `${API_ENDPOINTS.DOCUMENTS.BASE}?${params.toString()}`
    );
  }

  static async processDocument(documentId: string): Promise<DocumentProcessingResponse> {
    return apiClient.post<DocumentProcessingResponse>(
      `${API_ENDPOINTS.DOCUMENTS.BASE}/${documentId}/process`
    );
  }

  // Legacy endpoint for backward compatibility
  static async uploadPdfLegacy(file: File): Promise<{ message: string; file_id: string; filename: string; success: boolean }> {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.post<{ message: string; file_id: string; filename: string; success: boolean }>(
      API_ENDPOINTS.DOCUMENTS.UPLOAD_LEGACY,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  }
}

export const documentsApi = {
  uploadDocument: DocumentsApi.uploadDocument.bind(DocumentsApi),
  bulkUploadDocuments: DocumentsApi.bulkUploadDocuments.bind(DocumentsApi),
  getDocument: DocumentsApi.getDocument.bind(DocumentsApi),
  deleteDocument: DocumentsApi.deleteDocument.bind(DocumentsApi),
  listDocuments: DocumentsApi.listDocuments.bind(DocumentsApi),
  processDocument: DocumentsApi.processDocument.bind(DocumentsApi),
  uploadPdfLegacy: DocumentsApi.uploadPdfLegacy.bind(DocumentsApi),
};