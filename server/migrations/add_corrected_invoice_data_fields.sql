-- Migration: Add corrected invoice data fields to extracted_invoice_data table
-- Date: 2025-01-05
-- Description: Add JSONB field and metadata for storing corrected invoice data from correction agent

-- Add new columns for corrected invoice data
ALTER TABLE extracted_invoice_data 
ADD COLUMN IF NOT EXISTS corrected_invoice_data JSONB NULL,
ADD COLUMN IF NOT EXISTS correction_timestamp TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS corrected_by_human BOOLEAN NOT NULL DEFAULT FALSE;

-- Create index on corrected_invoice_data for better query performance
CREATE INDEX IF NOT EXISTS idx_extracted_invoice_data_corrected_data 
ON extracted_invoice_data USING GIN (corrected_invoice_data);

-- Create index on correction_timestamp for better query performance
CREATE INDEX IF NOT EXISTS idx_extracted_invoice_data_correction_timestamp 
ON extracted_invoice_data (correction_timestamp);

-- Create index on corrected_by_human for filtering
CREATE INDEX IF NOT EXISTS idx_extracted_invoice_data_corrected_by_human 
ON extracted_invoice_data (corrected_by_human);

-- Add comment to document the purpose of the new field
COMMENT ON COLUMN extracted_invoice_data.corrected_invoice_data IS 'JSONB field storing the complete corrected invoice data from the correction agent';
COMMENT ON COLUMN extracted_invoice_data.correction_timestamp IS 'Timestamp when the invoice data was corrected';
COMMENT ON COLUMN extracted_invoice_data.corrected_by_human IS 'Flag indicating whether human input was involved in the correction';