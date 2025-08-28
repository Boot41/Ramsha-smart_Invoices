export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface FilterOptions {
  search?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
}

export interface DashboardStats {
  totalInvoices: number;
  pendingInvoices: number;
  paidInvoices: number;
  overdueInvoices: number;
  totalRevenue: number;
  monthlyRevenue: number;
  activeContracts: number;
  activeBots: number;
}

export interface MenuItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  children?: MenuItem[];
  permission?: string;
}