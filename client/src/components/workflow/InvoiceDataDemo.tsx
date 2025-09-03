import React from 'react';
import ExtractedInvoiceData from './ExtractedInvoiceData';

// Sample invoice data based on your actual extracted data structure
const sampleInvoiceData = {
  processing_metadata: {
    original_invoice_data: {
      invoice_header: {
        invoice_id: "INV-382db96b-20250903-1756876970",
        invoice_date: "2025-09-03",
        due_date: "2025-09-13",
        contract_reference: "18325926-Rental-Agreement-1.pdf.pdf",
        workflow_id: "382db96b-482f-4ae3-a831-437be09bf6de",
        generated_at: "2025-09-03T10:52:50.069565"
      },
      parties: {
        client: {
          name: "Sri. P.M. Narayana Namboodri",
          email: null,
          address: "Laxmi Leela ground floor 3rd cross Ayyappa Nagar behind Ayyappa Temple, Jalahalli West, Bangalore - 15",
          phone: null,
          tax_id: null,
          role: "client"
        },
        service_provider: {
          name: "MR.K.Kuttan",
          email: null,
          address: "site No 152 Geethalayam OMH colong S.M. Road 1st main, T.Dasarahalli, Bangalore-57",
          phone: null,
          tax_id: null,
          role: "service_provider"
        }
      },
      contract_details: {
        contract_type: "rental_lease",
        start_date: "2008-12-05",
        end_date: "2009-11-04",
        effective_date: "2008-12-05"
      },
      payment_information: {
        amount: 4000.0,
        currency: "INR",
        frequency: "monthly",
        due_days: 10,
        late_fee: null,
        discount_terms: null,
        payment_method: "bank_transfer"
      },
      services_and_items: [
        {
          description: "Rental of premises at site No. 820 S.M. Road, Jalahalli West, Bangalore - 15, approximately 500 sft area of IInd floor with A.C. Sheet roof for non-residential purpose.",
          quantity: 1.0,
          unit_price: 4000.0,
          total_amount: 4000.0,
          unit: "monthly"
        }
      ],
      invoice_schedule: {
        frequency: "monthly",
        first_invoice_date: "2008-12-05",
        next_invoice_date: "2009-01-05"
      },
      additional_terms: {
        special_terms: "Agreement is for eleven months. A fresh agreement with mutual terms is required for extension. A three-month advance notice is required for termination by either party. The tenant is responsible for paying electricity and water charges separately.",
        notes: "A refundable security advance of Rs. 35,000 (Rupees thirty five thousand only) was paid by the tenant. This advance does not carry any interest and is refundable upon vacating the premises, after deducting any arrears for rent, electricity, or water.",
        late_fee_policy: "No late fee specified"
      },
      totals: {
        subtotal: 4000.0,
        tax_amount: 0.0,
        discount_amount: 0.0,
        total_amount: 4000.0
      },
      metadata: {
        generated_by: "smart_invoice_scheduler",
        agent_version: "1.0.0",
        user_id: "fd9b8b3f-2f94-4290-ad62-4661d6564974",
        confidence_score: 0.8,
        quality_score: 1.0,
        human_input_applied: false,
        validation_score: 1.0,
        processing_time_seconds: 36.403425,
        validation_passed: true
      },
      compliance: {
        generated_under: "Automated Smart Invoice Scheduler",
        human_reviewed: false,
        validation_passed: true,
        compliance_version: "1.0"
      }
    }
  }
};

const InvoiceDataDemo: React.FC = () => {
  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🧪 Invoice Data Visualization Demo
        </h1>
        <p className="text-gray-600">
          This demonstrates how your extracted rental agreement data will be displayed
        </p>
      </div>

      <ExtractedInvoiceData 
        invoiceData={sampleInvoiceData}
        workflowStatus={{ processing_status: 'SUCCESS', current_agent: 'completed' }}
      />
    </div>
  );
};

export default InvoiceDataDemo;