export interface RentInvoice {
  id: string;
  invoiceNumber: string;
  rentalAgreementId: string;
  tenantName: string;
  tenantEmail: string;
  propertyAddress: Address;
  monthlyRent: number;
  currency: string;
  dueDate: string;
  issueDate: string;
  status: InvoiceStatus;
  rentPeriod: {
    startDate: string;
    endDate: string;
  };
  items: RentInvoiceItem[];
  notes?: string;
  lateFee?: number;
  totalAmount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Invoice extends RentInvoice {} // Alias for backward compatibility

export interface RentInvoiceItem {
  id: string;
  description: string;
  amount: number;
  type: 'rent' | 'utilities' | 'maintenance' | 'late_fee' | 'other';
}

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export type InvoiceStatus = 
  | 'draft' 
  | 'pending' 
  | 'sent' 
  | 'viewed' 
  | 'paid' 
  | 'overdue' 
  | 'cancelled';

export interface RentInvoiceSchedule {
  id: string;
  rentalAgreementId: string;
  frequency: 'monthly' | 'quarterly' | 'annually';
  startDate: string;
  endDate?: string;
  nextSendDate: string;
  isActive: boolean;
  reminderDays: number[];
  autoGenerate: boolean;
  templateId?: string;
}

export interface InvoiceSchedule extends RentInvoiceSchedule {} // Alias

export interface RentInvoiceTemplate {
  id: string;
  name: string;
  description?: string;
  propertyType: 'apartment' | 'house' | 'commercial' | 'all';
  template: Partial<RentInvoice>;
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface InvoiceTemplate extends RentInvoiceTemplate {} // Alias