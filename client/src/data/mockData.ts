import type { 
  User, 
  Invoice, 
  Bot, 
  Contract, 
  DashboardStats, 
  MenuItem,
  Notification,
  RentalAgreement,
  RentInvoiceTemplate,
  RentInvoiceSchedule,
  RentInvoice
} from '../../types';

// Mock Users
export const mockUsers: User[] = [
  {
    id: '1',
    email: 'john.doe@example.com',
    firstName: 'John',
    lastName: 'Doe',
    role: 'user',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
    company: 'Acme Corp',
    phone: '+1-555-0123',
    isVerified: true,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-20T15:30:00Z',
  },
  {
    id: '2',
    email: 'admin@smartinvoice.com',
    firstName: 'Admin',
    lastName: 'User',
    role: 'admin',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
    isVerified: true,
    createdAt: '2024-01-01T09:00:00Z',
    updatedAt: '2024-01-25T12:00:00Z',
  }
];

// Mock Rental Invoices (legacy Invoice interface compatibility)
const mockInvoicesLegacy: any[] = [
  {
    id: 'inv-001',
    invoiceNumber: 'INV-2024-001',
    clientId: 'client-1',
    clientName: 'Acme Corporation',
    clientEmail: 'billing@acme.com',
    clientAddress: {
      street: '123 Business Ave',
      city: 'New York',
      state: 'NY',
      zipCode: '10001',
      country: 'USA'
    },
    amount: 2500.00,
    currency: 'USD',
    dueDate: '2024-03-15',
    issueDate: '2024-02-15',
    status: 'sent',
    items: [
      {
        id: 'item-1',
        description: 'Web Development Services',
        quantity: 1,
        unitPrice: 2000.00,
        totalPrice: 2000.00
      },
      {
        id: 'item-2',
        description: 'Domain & Hosting Setup',
        quantity: 1,
        unitPrice: 500.00,
        totalPrice: 500.00
      }
    ],
    notes: 'Payment due within 30 days',
    taxRate: 0.08,
    taxAmount: 200.00,
    totalAmount: 2700.00,
    paymentTerms: 'Net 30',
    createdAt: '2024-02-15T10:00:00Z',
    updatedAt: '2024-02-15T10:00:00Z'
  },
  {
    id: 'inv-002',
    invoiceNumber: 'INV-2024-002',
    clientId: 'client-2',
    clientName: 'Tech Solutions Inc',
    clientEmail: 'finance@techsolutions.com',
    clientAddress: {
      street: '456 Innovation Drive',
      city: 'San Francisco',
      state: 'CA',
      zipCode: '94105',
      country: 'USA'
    },
    amount: 1800.00,
    currency: 'USD',
    dueDate: '2024-03-20',
    issueDate: '2024-02-20',
    status: 'paid',
    items: [
      {
        id: 'item-3',
        description: 'Mobile App Consultation',
        quantity: 4,
        unitPrice: 450.00,
        totalPrice: 1800.00
      }
    ],
    taxRate: 0.0725,
    taxAmount: 130.50,
    totalAmount: 1930.50,
    paymentTerms: 'Net 30',
    createdAt: '2024-02-20T14:00:00Z',
    updatedAt: '2024-02-25T09:30:00Z'
  },
  {
    id: 'inv-003',
    invoiceNumber: 'INV-2024-003',
    clientId: 'client-3',
    clientName: 'Design Studio Pro',
    clientEmail: 'accounts@designstudio.com',
    clientAddress: {
      street: '789 Creative Blvd',
      city: 'Los Angeles',
      state: 'CA',
      zipCode: '90210',
      country: 'USA'
    },
    amount: 3200.00,
    currency: 'USD',
    dueDate: '2024-02-10',
    issueDate: '2024-01-10',
    status: 'overdue',
    items: [
      {
        id: 'item-4',
        description: 'UI/UX Design Package',
        quantity: 1,
        unitPrice: 3200.00,
        totalPrice: 3200.00
      }
    ],
    taxRate: 0.095,
    taxAmount: 304.00,
    totalAmount: 3504.00,
    paymentTerms: 'Net 30',
    createdAt: '2024-01-10T11:00:00Z',
    updatedAt: '2024-01-10T11:00:00Z'
  }
];

// Mock Bots
export const mockBots: Bot[] = [
  {
    id: 'bot-1',
    name: 'Invoice Automation Bot',
    description: 'Automatically generates and sends invoices based on completed projects',
    type: 'invoice_generator',
    status: 'active',
    configuration: {
      apiEndpoint: 'https://api.smartinvoice.com/v1/generate',
      settings: {
        autoSend: true,
        reminderDays: [7, 3, 1],
        template: 'default'
      },
      triggers: [
        {
          id: 'trigger-1',
          type: 'schedule',
          condition: 'daily',
          parameters: { time: '09:00' }
        }
      ],
      actions: [
        {
          id: 'action-1',
          type: 'send_invoice',
          parameters: { template: 'professional' }
        }
      ]
    },
    permissions: ['read_invoices', 'write_invoices', 'send_emails'],
    lastActivity: '2024-02-28T10:30:00Z',
    createdAt: '2024-01-15T12:00:00Z',
    updatedAt: '2024-02-25T16:45:00Z'
  },
  {
    id: 'bot-2',
    name: 'Payment Reminder Bot',
    description: 'Sends automated payment reminders for overdue invoices',
    type: 'payment_reminder',
    status: 'active',
    configuration: {
      settings: {
        reminderFrequency: 'weekly',
        escalation: true,
        maxReminders: 3
      },
      triggers: [
        {
          id: 'trigger-2',
          type: 'event',
          condition: 'invoice_overdue',
          parameters: { gracePeriod: 3 }
        }
      ],
      actions: [
        {
          id: 'action-2',
          type: 'send_reminder',
          parameters: { type: 'email', template: 'friendly' }
        }
      ]
    },
    permissions: ['read_invoices', 'send_emails'],
    lastActivity: '2024-02-28T08:15:00Z',
    createdAt: '2024-01-20T09:30:00Z',
    updatedAt: '2024-02-20T11:20:00Z'
  }
];

// Mock Rental Agreements
export const mockRentalAgreements: RentalAgreement[] = [
  {
    id: 'agreement-1',
    propertyTitle: 'Luxury Downtown Apartment',
    propertyAddress: '123 Main Street, Apt 4B, New York, NY 10001',
    tenantName: 'John Doe',
    tenantEmail: 'john.doe@example.com',
    tenantPhone: '+1-555-0123',
    landlordName: 'Jane Smith Properties',
    monthlyRent: 2500,
    securityDeposit: 2500,
    leaseStartDate: '2024-01-01',
    leaseEndDate: '2024-12-31',
    status: 'active',
    propertyType: 'apartment',
    documents: [
      {
        id: 'doc-1',
        name: 'Lease Agreement.pdf',
        type: 'application/pdf',
        url: '/documents/lease-agreement-1.pdf',
        uploadedAt: '2024-01-01T10:00:00Z',
        uploadedBy: 'Jane Smith'
      }
    ],
    terms: [
      {
        id: 'term-1',
        title: 'Monthly Rent Payment',
        description: 'Rent is due on the 1st of each month',
        type: 'payment',
        required: true
      },
      {
        id: 'term-2',
        title: 'Pet Policy',
        description: 'No pets allowed without prior written consent',
        type: 'pets',
        required: true
      }
    ],
    rentSchedule: [
      {
        id: 'payment-1',
        dueDate: '2024-01-01',
        amount: 2500,
        status: 'paid',
        paidDate: '2023-12-28',
        paidAmount: 2500,
        month: 'January 2024'
      },
      {
        id: 'payment-2',
        dueDate: '2024-02-01',
        amount: 2500,
        status: 'paid',
        paidDate: '2024-01-30',
        paidAmount: 2500,
        month: 'February 2024'
      },
      {
        id: 'payment-3',
        dueDate: '2024-03-01',
        amount: 2500,
        status: 'pending',
        month: 'March 2024'
      }
    ],
    createdBy: 'jane.smith@properties.com',
    createdAt: '2024-01-01T09:00:00Z',
    updatedAt: '2024-02-15T14:30:00Z'
  },
  {
    id: 'agreement-2',
    propertyTitle: 'Suburban Family House',
    propertyAddress: '456 Oak Avenue, Springfield, CA 90210',
    tenantName: 'Alice Johnson',
    tenantEmail: 'alice.johnson@example.com',
    tenantPhone: '+1-555-0456',
    landlordName: 'Bob Wilson Realty',
    monthlyRent: 3200,
    securityDeposit: 3200,
    leaseStartDate: '2024-02-01',
    leaseEndDate: '2025-01-31',
    status: 'active',
    propertyType: 'house',
    documents: [],
    terms: [
      {
        id: 'term-3',
        title: 'Lawn Maintenance',
        description: 'Tenant responsible for basic lawn care',
        type: 'maintenance',
        required: true
      }
    ],
    rentSchedule: [
      {
        id: 'payment-4',
        dueDate: '2024-02-01',
        amount: 3200,
        status: 'paid',
        paidDate: '2024-01-29',
        paidAmount: 3200,
        month: 'February 2024'
      },
      {
        id: 'payment-5',
        dueDate: '2024-03-01',
        amount: 3200,
        status: 'pending',
        month: 'March 2024'
      }
    ],
    createdBy: 'bob.wilson@realty.com',
    createdAt: '2024-02-01T10:00:00Z',
    updatedAt: '2024-02-01T10:00:00Z'
  }
];

// Mock Rent Invoice Templates
export const mockRentInvoiceTemplates: RentInvoiceTemplate[] = [
  {
    id: 'template-1',
    name: 'Standard Apartment Rent',
    description: 'Default template for apartment rentals',
    propertyType: 'apartment',
    template: {
      currency: 'USD',
      items: [
        {
          id: 'item-rent',
          description: 'Monthly Rent',
          amount: 0,
          type: 'rent'
        }
      ],
      notes: 'Payment is due on the 1st of each month. Late fees apply after 5 days.'
    },
    isDefault: true,
    createdAt: '2024-01-01T09:00:00Z',
    updatedAt: '2024-01-01T09:00:00Z'
  },
  {
    id: 'template-2',
    name: 'House Rental with Utilities',
    description: 'Template for house rentals including utilities',
    propertyType: 'house',
    template: {
      currency: 'USD',
      items: [
        {
          id: 'item-rent',
          description: 'Monthly Rent',
          amount: 0,
          type: 'rent'
        },
        {
          id: 'item-utilities',
          description: 'Utilities (Water/Trash)',
          amount: 150,
          type: 'utilities'
        }
      ],
      notes: 'Rent includes water and trash services. Electricity and gas are tenant responsibility.'
    },
    isDefault: false,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z'
  }
];

// Mock Rent Invoice Schedules
export const mockRentInvoiceSchedules: RentInvoiceSchedule[] = [
  {
    id: 'schedule-1',
    rentalAgreementId: 'agreement-1',
    frequency: 'monthly',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    nextSendDate: '2024-03-25',
    isActive: true,
    reminderDays: [7, 3, 1],
    autoGenerate: true,
    templateId: 'template-1'
  },
  {
    id: 'schedule-2',
    rentalAgreementId: 'agreement-2',
    frequency: 'monthly',
    startDate: '2024-02-01',
    endDate: '2025-01-31',
    nextSendDate: '2024-03-25',
    isActive: true,
    reminderDays: [5, 2],
    autoGenerate: true,
    templateId: 'template-2'
  }
];

// Mock Rent Invoices
export const mockRentInvoices: RentInvoice[] = [
  {
    id: 'rent-inv-1',
    invoiceNumber: 'RENT-2024-001',
    rentalAgreementId: 'agreement-1',
    tenantName: 'John Doe',
    tenantEmail: 'john.doe@example.com',
    propertyAddress: {
      street: '123 Main Street, Apt 4B',
      city: 'New York',
      state: 'NY',
      zipCode: '10001',
      country: 'USA'
    },
    monthlyRent: 2500,
    currency: 'USD',
    dueDate: '2024-03-01',
    issueDate: '2024-02-25',
    status: 'sent',
    rentPeriod: {
      startDate: '2024-03-01',
      endDate: '2024-03-31'
    },
    items: [
      {
        id: 'item-1',
        description: 'Monthly Rent - March 2024',
        amount: 2500,
        type: 'rent'
      }
    ],
    notes: 'Payment is due on the 1st of each month. Late fees apply after 5 days.',
    totalAmount: 2500,
    createdAt: '2024-02-25T09:00:00Z',
    updatedAt: '2024-02-25T09:00:00Z'
  },
  {
    id: 'rent-inv-2',
    invoiceNumber: 'RENT-2024-002',
    rentalAgreementId: 'agreement-2',
    tenantName: 'Alice Johnson',
    tenantEmail: 'alice.johnson@example.com',
    propertyAddress: {
      street: '456 Oak Avenue',
      city: 'Springfield',
      state: 'CA',
      zipCode: '90210',
      country: 'USA'
    },
    monthlyRent: 3200,
    currency: 'USD',
    dueDate: '2024-03-01',
    issueDate: '2024-02-25',
    status: 'sent',
    rentPeriod: {
      startDate: '2024-03-01',
      endDate: '2024-03-31'
    },
    items: [
      {
        id: 'item-1',
        description: 'Monthly Rent - March 2024',
        amount: 3200,
        type: 'rent'
      },
      {
        id: 'item-2',
        description: 'Utilities (Water/Trash)',
        amount: 150,
        type: 'utilities'
      }
    ],
    notes: 'Rent includes water and trash services. Electricity and gas are tenant responsibility.',
    totalAmount: 3350,
    createdAt: '2024-02-25T10:00:00Z',
    updatedAt: '2024-02-25T10:00:00Z'
  }
];

// Mock Contracts (legacy compatibility)
const mockContractsLegacy: any[] = [
  {
    id: 'contract-1',
    title: 'Website Development Agreement',
    description: 'Full-stack web application development for e-commerce platform',
    type: 'service_agreement',
    status: 'active',
    clientId: 'client-1',
    clientName: 'Acme Corporation',
    value: 50000,
    currency: 'USD',
    startDate: '2024-01-01',
    endDate: '2024-06-30',
    terms: [
      {
        id: 'term-1',
        title: 'Payment Schedule',
        description: '50% upfront, 25% at milestone 1, 25% on completion',
        type: 'payment',
        required: true
      }
    ],
    documents: [
      {
        id: 'doc-1',
        name: 'Contract Agreement.pdf',
        type: 'application/pdf',
        url: '/documents/contract-1-agreement.pdf',
        uploadedAt: '2024-01-01T10:00:00Z',
        uploadedBy: 'John Doe'
      }
    ],
    milestones: [
      {
        id: 'milestone-1',
        title: 'Frontend Development',
        description: 'Complete frontend implementation',
        dueDate: '2024-03-15',
        status: 'in_progress',
        value: 12500
      }
    ],
    approvals: [
      {
        id: 'approval-1',
        approverName: 'Jane Smith',
        approverRole: 'Project Manager',
        status: 'approved',
        approvedAt: '2024-01-01T15:30:00Z'
      }
    ],
    createdBy: 'admin',
    createdAt: '2024-01-01T09:00:00Z',
    updatedAt: '2024-02-15T14:20:00Z'
  }
];

// Mock Dashboard Stats
export const mockDashboardStats: DashboardStats = {
  totalInvoices: 147,
  pendingInvoices: 23,
  paidInvoices: 98,
  overdueInvoices: 8,
  totalRevenue: 245000,
  monthlyRevenue: 32000,
  activeContracts: 12,
  activeBots: 5
};

// Mock Menu Items
export const mockMenuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: '📊',
    path: '/dashboard'
  },
  {
    id: 'invoices',
    label: 'Invoices',
    icon: '📄',
    path: '/invoices',
    children: [
      {
        id: 'all-invoices',
        label: 'All Invoices',
        icon: '📋',
        path: '/invoices/all'
      },
      {
        id: 'create-invoice',
        label: 'Create Invoice',
        icon: '➕',
        path: '/invoices/create'
      },
      {
        id: 'schedule-invoice',
        label: 'Schedule Invoice',
        icon: '⏰',
        path: '/invoices/schedule'
      }
    ]
  },
  {
    id: 'bots',
    label: 'Bot Management',
    icon: '🤖',
    path: '/bots',
    children: [
      {
        id: 'bot-list',
        label: 'All Bots',
        icon: '📝',
        path: '/bots/list'
      },
      {
        id: 'bot-settings',
        label: 'Bot Settings',
        icon: '⚙️',
        path: '/bots/settings'
      }
    ]
  },
  {
    id: 'contracts',
    label: 'Contracts',
    icon: '📋',
    path: '/contracts'
  },
  {
    id: 'marketplace',
    label: 'Marketplace',
    icon: '🛒',
    path: '/marketplace'
  },
  {
    id: 'admin',
    label: 'Admin',
    icon: '👥',
    path: '/admin',
    permission: 'admin',
    children: [
      {
        id: 'admin-home',
        label: 'Admin Dashboard',
        icon: '🏠',
        path: '/admin/home'
      },
      {
        id: 'approvals',
        label: 'Approvals',
        icon: '✅',
        path: '/admin/approvals'
      }
    ]
  }
];

// Mock Notifications
export const mockNotifications: Notification[] = [
  {
    id: 'notif-1',
    type: 'success',
    title: 'Payment Received',
    message: 'Invoice INV-2024-002 has been paid by Tech Solutions Inc',
    isRead: false,
    createdAt: '2024-02-28T10:15:00Z'
  },
  {
    id: 'notif-2',
    type: 'warning',
    title: 'Invoice Overdue',
    message: 'Invoice INV-2024-003 is now 18 days overdue',
    isRead: false,
    createdAt: '2024-02-28T09:00:00Z'
  },
  {
    id: 'notif-3',
    type: 'info',
    title: 'Bot Activity',
    message: 'Payment Reminder Bot sent 3 reminders today',
    isRead: true,
    createdAt: '2024-02-27T18:30:00Z'
  }
];

// Export all mock data - already exported above with definitions

// Export aliases for backward compatibility
export { mockRentInvoices as mockInvoices };
export { mockRentalAgreements as mockContracts };

// Legacy exports (will be removed in future versions)
export { mockInvoicesLegacy };
export { mockContractsLegacy };