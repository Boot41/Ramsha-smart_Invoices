export interface Bot {
  id: string;
  name: string;
  description: string;
  type: BotType;
  status: BotStatus;
  configuration: BotConfiguration;
  permissions: BotPermission[];
  lastActivity: string;
  createdAt: string;
  updatedAt: string;
}

export type BotType = 
  | 'invoice_generator' 
  | 'payment_reminder' 
  | 'data_processor' 
  | 'report_generator' 
  | 'customer_support';

export type BotStatus = 'active' | 'inactive' | 'error' | 'maintenance';

export interface BotConfiguration {
  apiEndpoint?: string;
  apiKey?: string;
  webhookUrl?: string;
  settings: Record<string, any>;
  triggers: BotTrigger[];
  actions: BotAction[];
}

export interface BotTrigger {
  id: string;
  type: 'schedule' | 'event' | 'webhook' | 'manual';
  condition: string;
  parameters: Record<string, any>;
}

export interface BotAction {
  id: string;
  type: 'send_invoice' | 'send_reminder' | 'generate_report' | 'update_status';
  parameters: Record<string, any>;
}

export type BotPermission = 
  | 'read_invoices' 
  | 'write_invoices' 
  | 'send_emails' 
  | 'access_reports' 
  | 'manage_clients';

export interface BotActivity {
  id: string;
  botId: string;
  action: string;
  status: 'success' | 'error' | 'pending';
  message: string;
  data?: Record<string, any>;
  timestamp: string;
}