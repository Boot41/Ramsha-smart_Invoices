export interface RentalAgreement {
  id: string;
  propertyTitle: string;
  propertyAddress: string;
  tenantName: string;
  tenantEmail: string;
  tenantPhone: string;
  landlordName: string;
  monthlyRent: number;
  securityDeposit: number;
  leaseStartDate: string;
  leaseEndDate: string;
  status: RentalStatus;
  propertyType: PropertyType;
  documents: ContractDocument[];
  terms: RentalTerm[];
  rentSchedule: RentPayment[];
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface Contract extends RentalAgreement {} // Alias for backward compatibility

export type PropertyType = 
  | 'apartment' 
  | 'house' 
  | 'studio' 
  | 'townhouse' 
  | 'condo' 
  | 'commercial';

export type RentalStatus = 
  | 'draft' 
  | 'pending_signature' 
  | 'active' 
  | 'expired' 
  | 'terminated' 
  | 'renewed';

export type ContractType = PropertyType; // Alias
export type ContractStatus = RentalStatus; // Alias

export interface RentalTerm {
  id: string;
  title: string;
  description: string;
  type: 'payment' | 'maintenance' | 'pets' | 'utilities' | 'termination' | 'other';
  required: boolean;
}

export interface ContractTerm extends RentalTerm {} // Alias

export interface ContractDocument {
  id: string;
  name: string;
  type: string;
  url: string;
  uploadedAt: string;
  uploadedBy: string;
}

export interface RentPayment {
  id: string;
  dueDate: string;
  amount: number;
  status: 'pending' | 'paid' | 'overdue' | 'partial';
  paidDate?: string;
  paidAmount?: number;
  month: string;
}

export interface ContractMilestone {
  id: string;
  title: string;
  description: string;
  dueDate: string;
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  value?: number;
}

export interface RentalApproval {
  id: string;
  approverName: string;
  approverRole: 'tenant' | 'landlord' | 'witness';
  status: 'pending' | 'signed' | 'rejected';
  comments?: string;
  signedAt?: string;
  signatureUrl?: string;
}

export interface ContractApproval extends RentalApproval {} // Alias