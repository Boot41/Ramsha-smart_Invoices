-- Smart Invoice Scheduler - Sample Database Content
-- Run this file to populate your PostgreSQL database with sample data

-- First, ensure tables exist (run init_db.py first)

-- Insert sample users
INSERT INTO users (id, email, first_name, last_name, phone, password_hash, role, status, email_verified, created_at)
VALUES 
  ('user-001', 'tenant1@example.com', 'John', 'Doe', '+1-555-0101', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'TENANT', 'active', true, NOW()),
  ('user-002', 'renter1@example.com', 'Jane', 'Smith', '+1-555-0102', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'RENT_PAYER', 'active', true, NOW()),
  ('user-003', 'tenant2@example.com', 'Bob', 'Johnson', '+1-555-0103', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'TENANT', 'active', true, NOW())
ON CONFLICT (email) DO NOTHING;

-- Insert sample addresses
INSERT INTO addresses (id, street, building_number, city, state, postal_code, country, created_at)
VALUES 
  ('addr-001', 'Main Street', '123', 'New York', 'NY', '10001', 'USA', NOW()),
  ('addr-002', 'Oak Avenue', '456', 'Los Angeles', 'CA', '90210', 'USA', NOW()),
  ('addr-003', 'Pine Road', '789', 'Chicago', 'IL', '60601', 'USA', NOW())
ON CONFLICT (id) DO NOTHING;

-- Insert sample security events
INSERT INTO security_events (id, event_type, user_id, email, ip_address, timestamp)
VALUES 
  ('sec-001', 'login_success', 'user-001', 'tenant1@example.com', '192.168.1.100', NOW()),
  ('sec-002', 'login_success', 'user-002', 'renter1@example.com', '192.168.1.101', NOW()),
  ('sec-003', 'password_change', 'user-003', 'tenant2@example.com', '192.168.1.102', NOW());

-- Insert sample user sessions
INSERT INTO user_sessions (id, user_id, session_token, ip_address, is_active, expires_at, created_at)
VALUES 
  ('sess-001', 'user-001', 'token_abc123', '192.168.1.100', true, NOW() + INTERVAL '24 hours', NOW()),
  ('sess-002', 'user-002', 'token_def456', '192.168.1.101', true, NOW() + INTERVAL '24 hours', NOW());

-- Insert sample invoices
INSERT INTO invoices (
  id, invoice_number, workflow_id, user_id, invoice_date, due_date, status,
  client_name, client_email, client_address, service_provider_name, 
  service_provider_email, subtotal, tax_amount, total_amount, currency,
  contract_title, contract_type, contract_reference, invoice_data,
  generated_by_agent, confidence_score, quality_score, human_reviewed, created_at
)
VALUES 
  (
    'inv-001', 'INV-2024-001', 'wf-12345', 'user-001', 
    '2024-01-15'::date, '2024-02-15'::date, 'GENERATED',
    'ABC Corporation', 'billing@abc-corp.com', '123 Business St, New York, NY 10001',
    'Property Management LLC', 'contact@propman.com',
    1200.00, 120.00, 1320.00, 'USD',
    'Office Lease Agreement', 'commercial_lease', 'LEASE-2024-001',
    '{"items": [{"description": "Monthly Office Rent", "amount": 1200.00, "quantity": 1}], "terms": "Net 30", "notes": "Generated from contract processing"}',
    'correction_agent', 0.95, 0.89, false, NOW()
  ),
  (
    'inv-002', 'INV-2024-002', 'wf-12346', 'user-002',
    '2024-01-20'::date, '2024-02-20'::date, 'SENT',
    'Tech Startup Inc', 'finance@techstartup.com', '456 Innovation Blvd, San Francisco, CA 94105',
    'Downtown Properties', 'billing@downtown.com',
    2500.00, 200.00, 2700.00, 'USD',
    'Commercial Space Rental', 'commercial_lease', 'LEASE-2024-002',
    '{"items": [{"description": "Monthly Commercial Rent", "amount": 2500.00, "quantity": 1}], "terms": "Net 15", "notes": "High-confidence generation"}',
    'correction_agent', 0.92, 0.91, true, NOW()
  ),
  (
    'inv-003', 'INV-2024-003', 'wf-12347', 'user-003',
    '2024-01-25'::date, '2024-02-25'::date, 'DRAFT',
    'Family Restaurant LLC', 'owner@familyrest.com', '789 Food Street, Chicago, IL 60601',
    'Commercial Realty Group', 'leasing@crg.com',
    1800.00, 144.00, 1944.00, 'USD',
    'Restaurant Lease Agreement', 'commercial_lease', 'LEASE-2024-003',
    '{"items": [{"description": "Monthly Restaurant Rent", "amount": 1800.00, "quantity": 1}], "terms": "Net 30", "notes": "Requires review"}',
    'correction_agent', 0.87, 0.85, false, NOW()
  );

-- Insert sample invoice templates
INSERT INTO invoice_templates (
  id, invoice_id, template_name, component_name, template_type,
  file_path, component_code, generated_by, model_used, is_active, created_at
)
VALUES 
  (
    'tmpl-001', 'inv-001', 'Professional Invoice Template', 'InvoiceAbc001',
    'Professional Invoice Template',
    '/home/ramsha/Documents/smart-invoice-scheduler/client/src/components/invoices/invoice-abc-001.tsx',
    '',
    'ui_invoice_generator', 'claude-3.5-sonnet', true, NOW()
  ),
  (
    'tmpl-002', 'inv-002', 'Modern Invoice Design', 'InvoiceTech002',
    'Modern Invoice Template',
    '/home/ramsha/Documents/smart-invoice-scheduler/client/src/components/invoices/invoice-tech-002.tsx',
    '',
    'ui_invoice_generator', 'claude-3.5-sonnet', true, NOW()
  ),
  (
    'tmpl-003', 'inv-003', 'Classic Invoice Layout', 'InvoiceRestaurant003',
    'Classic Invoice Template', 
    '/home/ramsha/Documents/smart-invoice-scheduler/client/src/components/invoices/invoice-restaurant-003.tsx',
    '',
    'ui_invoice_generator', 'claude-3.5-sonnet', true, NOW()
  );
