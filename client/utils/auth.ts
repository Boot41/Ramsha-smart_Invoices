import { TOKEN_STORAGE_KEY } from '../api/config';

export function clearAllAuthData(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  // Add any other auth-related data clearing here if needed
}
