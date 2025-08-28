export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    // Add other auth endpoints as needed
  },
  DOCUMENTS: {
    BASE: '/documents',
    UPLOAD: '/documents/upload',
    BULK_UPLOAD: '/documents/upload/bulk',
    UPLOAD_LEGACY: '/documents/upload-contract', // Legacy endpoint
  },
  // Add other API endpoints as needed
};

export const TOKEN_STORAGE_KEY = 'authToken';