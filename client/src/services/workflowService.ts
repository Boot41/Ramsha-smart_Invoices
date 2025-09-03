/**
 * Workflow API Service
 * Handles HTTP requests to the agentic workflow backend
 */

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000/api/v1/orchestrator'
  : '/api/v1/orchestrator';

export interface WorkflowRequest {
  user_id: string;
  contract_name: string;
  max_attempts?: number;
  options?: Record<string, any>;
}

export interface WorkflowResponse {
  workflow_id: string;
  status: string;
  message: string;
  quality_score?: number;
  confidence_level?: number;
  attempt_count?: number;
  estimated_completion_time?: string;
}

export interface WorkflowStatus {
  workflow_id: string;
  status: string;
  current_agent: string;
  progress_percentage: number;
  quality_score: number;
  confidence_level: number;
  validation_results?: any;
  human_input_request?: any;
  error_message?: string;
  estimated_completion_time?: string;
  created_at: string;
  updated_at: string;
}

export interface ActiveWorkflow {
  workflow_id: string;
  user_id: string;
  contract_name: string;
  status: string;
  current_agent: string;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
}

class WorkflowAPIService {
  private async getAuthHeaders(): Promise<HeadersInit> {
    // Get JWT token from localStorage using the correct key
    const token = localStorage.getItem('authToken');
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  }

  private async getFormDataHeaders(): Promise<HeadersInit> {
    const token = localStorage.getItem('authToken');
    return {
      // Don't set Content-Type for FormData - browser will set it with boundary
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  }

  /**
   * Start a new agentic workflow
   */
  async startWorkflow(
    contractFile: File, 
    contractName: string, 
    userId: string, 
    options: Record<string, any> = {}
  ): Promise<WorkflowResponse> {
    try {
      const formData = new FormData();
      formData.append('contract_file', contractFile);
      formData.append('contract_name', contractName);
      formData.append('user_id', userId);
      formData.append('max_attempts', '3');
      formData.append('options', JSON.stringify(options));

      const response = await fetch(`${API_BASE_URL}/workflow/invoice/start`, {
        method: 'POST',
        headers: await this.getFormDataHeaders(),
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to start workflow: ${response.status} ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error starting workflow:', error);
      throw error;
    }
  }

  /**
   * Get workflow status
   */
  async getWorkflowStatus(workflowId: string): Promise<WorkflowStatus> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/${workflowId}/status`, {
        headers: await this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get workflow status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error getting workflow status:', error);
      throw error;
    }
  }

  /**
   * Get final invoice JSON data from completed workflow
   */
  async getWorkflowInvoiceData(workflowId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/${workflowId}/invoice`, {
        headers: await this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get invoice data: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error getting invoice data:', error);
      throw error;
    }
  }

  /**
   * Get UI template from completed workflow
   */
  async getWorkflowUITemplate(workflowId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/${workflowId}/ui-template`, {
        headers: await this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get UI template: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error getting UI template:', error);
      throw error;
    }
  }

  /**
   * Cancel running workflow
   */
  async cancelWorkflow(workflowId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/${workflowId}/cancel`, {
        method: 'DELETE',
        headers: await this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to cancel workflow: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error cancelling workflow:', error);
      throw error;
    }
  }

  /**
   * List active workflows
   */
  async listActiveWorkflows(userId?: string): Promise<ActiveWorkflow[]> {
    try {
      const url = new URL(`${API_BASE_URL}/workflows/active`);
      if (userId) {
        url.searchParams.append('user_id', userId);
      }

      const response = await fetch(url.toString(), {
        headers: await this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to list workflows: ${response.status}`);
      }

      const result = await response.json();
      return result.workflows || [];
    } catch (error) {
      console.error('❌ Error listing workflows:', error);
      throw error;
    }
  }

  /**
   * Check orchestrator system health
   */
  async checkHealth(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/health`);

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error checking health:', error);
      throw error;
    }
  }

  /**
   * Create test workflow (for development)
   */
  async createTestWorkflow(): Promise<WorkflowResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/test`, {
        method: 'POST',
        headers: await this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to create test workflow: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error creating test workflow:', error);
      throw error;
    }
  }

  /**
   * Submit human input for workflow validation
   */
  async submitHumanInput(
    workflowId: string, 
    fieldValues: Record<string, any>, 
    userNotes: string = ''
  ): Promise<any> {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/human-input/submit`, {
        method: 'POST',
        headers: await this.getAuthHeaders(),
        body: JSON.stringify({
          workflow_id: workflowId,
          field_values: fieldValues,
          user_notes: userNotes
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to submit human input: ${response.status} ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error submitting human input:', error);
      throw error;
    }
  }

  /**
   * Get current user ID from localStorage or JWT token
   */
  getCurrentUserId(): string {
    // First try to get from stored userId
    const storedUserId = localStorage.getItem('userId');
    if (storedUserId && storedUserId !== 'current_user') {
      return storedUserId;
    }

    // Try to get from stored user object
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        return user.id || user.user_id || user.email;
      } catch {
        // Continue to JWT token method
      }
    }

    // Try to extract from JWT token
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.sub || payload.user_id || payload.id || payload.email;
      } catch {
        // JWT parsing failed
      }
    }

    // If all else fails, throw an error instead of returning a non-existent user
    throw new Error('Unable to determine current user ID. Please log in again.');
  }
}

// Create singleton instance
export const workflowAPI = new WorkflowAPIService();

export default workflowAPI;