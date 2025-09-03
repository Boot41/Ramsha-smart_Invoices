/**
 * WebSocket Service for Real-time Workflow Communication
 * Handles real-time updates for agentic workflow processing
 */

export interface WorkflowState {
  workflow_id: string;
  contract_name?: string;
  user_id?: string;
  processing_status?: string;
  validation_results?: any;
  current_agent?: string;
  quality_score?: number;
  confidence_level?: number;
  human_input_request?: any;
  final_invoice_json?: any;
  ui_invoice_template?: any;
}

export interface WorkflowEvent {
  type: string;
  data: any;
  timestamp?: string;
}

export interface HumanInputRequest {
  fields: Array<{
    name: string;
    value: any;
    label: string;
    type: string;
    required: boolean;
    validation_message?: string;
  }>;
  instructions: string;
  context: any;
}

type EventHandler = (event: WorkflowEvent) => void;

class WorkflowWebSocketService {
  private ws: WebSocket | null = null;
  private eventHandlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private workflowId: string | null = null;
  private isConnecting = false;
  
  // Server configuration
  private getWebSocketUrl(workflowId: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = process.env.NODE_ENV === 'development' ? '8000' : window.location.port;
    return `${protocol}//${host}:${port}/api/v1/orchestrator/ws/workflow/${workflowId}/realtime`;
  }
  
  /**
   * Connect to workflow WebSocket
   */
  async connect(workflowId: string): Promise<boolean> {
    if (this.isConnecting) {
      console.log('⏳ Already connecting to WebSocket...');
      return false;
    }
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN && this.workflowId === workflowId) {
      console.log('🔌 WebSocket already connected to workflow:', workflowId);
      return true;
    }
    
    this.isConnecting = true;
    this.workflowId = workflowId;
    
    try {
      const wsUrl = this.getWebSocketUrl(workflowId);
      console.log('🔗 Connecting to workflow WebSocket:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected to workflow:', workflowId);
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Send initial status request
        this.sendMessage('get_status', {});
        
        this.emit('connection_established', { workflowId });
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', message);
          this.handleMessage(message);
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason);
        this.isConnecting = false;
        this.emit('connection_closed', { workflowId, code: event.code, reason: event.reason });
        
        // Attempt reconnection for non-intentional closures
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect(workflowId);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.isConnecting = false;
        this.emit('connection_error', { workflowId, error });
      };
      
      return true;
      
    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error);
      this.isConnecting = false;
      this.emit('connection_error', { workflowId, error });
      return false;
    }
  }
  
  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      console.log('🔌 Disconnecting WebSocket...');
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.workflowId = null;
    this.reconnectAttempts = 0;
  }
  
  /**
   * Send message to server
   */
  sendMessage(type: string, data: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('❌ Cannot send message: WebSocket not connected');
      return;
    }
    
    const message = {
      type,
      data,
      timestamp: new Date().toISOString()
    };
    
    console.log('📤 Sending WebSocket message:', message);
    this.ws.send(JSON.stringify(message));
  }
  
  /**
   * Submit human input for validation using HTTP endpoint
   */
  async submitHumanInput(fieldValues: Record<string, any>, userNotes: string = ''): Promise<boolean> {
    if (!this.workflowId) {
      console.error('❌ No workflow ID available for human input submission');
      return false;
    }

    try {
      const API_BASE = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000' 
        : window.location.origin;
      
      const response = await fetch(`${API_BASE}/api/v1/human-input/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow_id: this.workflowId,
          field_values: fieldValues,
          user_notes: userNotes
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Human input submission failed:', errorText);
        return false;
      }

      const result = await response.json();
      console.log('✅ Human input submitted successfully:', result);
      return true;
      
    } catch (error) {
      console.error('❌ Error submitting human input:', error);
      return false;
    }
  }

  /**
   * Submit general human input for waiting workflows
   * Uses the new HTTP endpoint for general human input
   */
  async submitGeneralHumanInput(taskId: string, userInput: string): Promise<boolean> {
    try {
      const API_BASE = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000' 
        : window.location.origin;
      
      const response = await fetch(`${API_BASE}/api/v1/human-input/input`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId,
          user_input: userInput
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit human input');
      }

      const result = await response.json();
      console.log('✅ General human input submitted successfully:', result);
      return true;
      
    } catch (error) {
      console.error('❌ Failed to submit general human input:', error);
      throw error;
    }
  }

  /**
   * Request workflow pause (for debugging/manual intervention)
   */
  pauseWorkflow(): void {
    this.sendMessage('workflow_control', {
      action: 'pause'
    });
  }

  /**
   * Request workflow resume
   */
  resumeWorkflow(): void {
    this.sendMessage('workflow_control', {
      action: 'resume'
    });
  }
  
  /**
   * Request current workflow status
   */
  requestStatus(): void {
    this.sendMessage('get_status', {});
  }
  
  /**
   * Send ping to keep connection alive
   */
  ping(): void {
    this.sendMessage('ping', {});
  }
  
  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: any): void {
    const eventType = message.event_type || message.type || 'unknown';
    const eventData = message.data || message;
    
    // Special handling for different event types
    switch (eventType) {
      case 'workflow_status':
        this.emit('status_update', eventData);
        break;
        
      case 'agent_transition':
        this.emit('agent_change', eventData);
        break;
        
      case 'validation_results':
        this.emit('validation_update', eventData);
        break;
        
      case 'human_input_required':
        this.emit('human_input_needed', eventData);
        break;
        
      case 'human_input_acknowledged':
        this.emit('input_acknowledged', eventData);
        break;
        
      case 'human_input_processed':
        this.emit('input_processed', eventData);
        break;
        
      case 'human_input_received':
        this.emit('input_processed', eventData);
        break;
        
      case 'waiting_for_human_input':
        this.emit('workflow_waiting_input', eventData);
        break;
        
      case 'workflow_paused':
        this.emit('workflow_paused', eventData);
        break;
        
      case 'workflow_resumed':
        this.emit('workflow_resumed', eventData);
        break;
        
      case 'workflow_completed':
        this.emit('workflow_complete', eventData);
        break;
        
      case 'workflow_failed':
        this.emit('workflow_error', eventData);
        break;
        
      case 'progress_update':
        this.emit('progress', eventData);
        break;
        
      case 'error':
        this.emit('error', eventData);
        break;
        
      case 'pong':
        this.emit('pong', eventData);
        break;
        
      default:
        console.log('📨 Unhandled WebSocket event:', eventType, eventData);
        this.emit(eventType, eventData);
    }
  }
  
  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(workflowId: string): void {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`⏳ Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        console.log(`🔄 Reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        this.connect(workflowId);
      }
    }, delay);
  }
  
  /**
   * Add event listener
   */
  on(eventType: string, handler: EventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(handler);
  }
  
  /**
   * Remove event listener
   */
  off(eventType: string, handler: EventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.eventHandlers.delete(eventType);
      }
    }
  }
  
  /**
   * Emit event to all listeners
   */
  private emit(eventType: string, data: any): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const event: WorkflowEvent = {
        type: eventType,
        data,
        timestamp: new Date().toISOString()
      };
      
      handlers.forEach(handler => {
        try {
          handler(event);
        } catch (error) {
          console.error('❌ Error in event handler:', error);
        }
      });
    }
  }
  
  /**
   * Get connection status
   */
  getConnectionStatus(): {
    connected: boolean;
    connecting: boolean;
    workflowId: string | null;
    readyState: number | null;
  } {
    return {
      connected: this.ws?.readyState === WebSocket.OPEN,
      connecting: this.isConnecting,
      workflowId: this.workflowId,
      readyState: this.ws?.readyState || null
    };
  }
}

// Create singleton instance
export const workflowWebSocket = new WorkflowWebSocketService();

// Export types and service
export { WorkflowWebSocketService };
export default workflowWebSocket;