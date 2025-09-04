import { TOKEN_STORAGE_KEY } from './config';

interface ApiClientOptions {
  requiresAuth?: boolean;
  isMultipart?: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiFetch<T>(
  url: string,
  method: string,
  data?: any,
  options?: ApiClientOptions
): Promise<T> {
  const headers: HeadersInit = {};
  const config: RequestInit = {
    method,
  };

  if (options?.requiresAuth !== false) {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  if (data) {
    if (options?.isMultipart) {
      config.body = data; // data is FormData
    } else {
      headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(data);
    }
  }

  config.headers = headers;

  const response = await fetch(`${API_BASE_URL}${url}`, config);

  if (!response.ok) {
    // Handle HTTP errors
    const errorData = await response.json().catch(() => ({ message: response.statusText }));
    
    // Create a custom error that preserves the response structure
    const apiError = new Error(errorData.detail || errorData.message || 'API request failed');
    (apiError as any).response = {
      status: response.status,
      data: errorData
    };
    throw apiError;
  }

  // For successful responses, try to parse JSON, but handle cases with no content
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json() as Promise<T>;
  } else {
    return {} as T; // Return empty object for non-JSON responses (e.g., 204 No Content)
  }
}

export const apiClient = {
  get: <T>(url: string, options?: ApiClientOptions) => apiFetch<T>(url, 'GET', undefined, options),
  post: <T>(url: string, data: any, options?: ApiClientOptions) => apiFetch<T>(url, 'POST', data, options),
  put: <T>(url: string, data: any, options?: ApiClientOptions) => apiFetch<T>(url, 'PUT', data, options),
  delete: <T>(url: string, options?: ApiClientOptions) => apiFetch<T>(url, 'DELETE', undefined, options),
};
