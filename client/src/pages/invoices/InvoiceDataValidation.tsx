import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { workflowAPI } from '../../services/workflowService';

interface ValidationField {
  key: string;
  value: any;
  requiresValidation: boolean;
  validationMessage?: string;
  type?: 'text' | 'number' | 'date' | 'email' | 'textarea';
  label?: string;
}

interface InvoiceData {
  [key: string]: any;
}

const InvoiceDataValidation: React.FC = () => {
  const { contractId } = useParams<{ contractId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [invoiceData, setInvoiceData] = useState<InvoiceData>({});
  const [validationFields, setValidationFields] = useState<ValidationField[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [contractName, setContractName] = useState<string>('');

  // Get data from navigation state or fetch from API
  useEffect(() => {
    const initializeData = async () => {
      console.log('🚀 InvoiceDataValidation component initializing...');
      console.log('📍 Contract ID:', contractId);
      console.log('📍 Location state:', location.state);
      
      setIsLoading(true);
      try {
        // Get data from navigation state if available
        const navigationState = location.state as any;
        
        if (navigationState?.validationData) {
          console.log('✅ Using navigation state data');
          // Use data passed from workflow
          const { validationData, workflowId: navWorkflowId, contractName: navContractName } = navigationState;
          
          setWorkflowId(navWorkflowId);
          setContractName(navContractName || '');
          
          // Extract invoice data and validation fields from workflow data
          console.log('📋 Full validation data:', validationData);
          console.log('🔍 Available keys in validation data:', Object.keys(validationData));
          
          // Use the correct field names from ValidationRequirementsResponse
          // Prioritize unified_invoice_data format
          const extractedData = validationData.current_data || 
                               validationData.extracted_data || 
                               validationData.invoice_data || 
                               {};
          
          // If the data contains unified format structures, flatten them for display
          let flattenedData = extractedData;
          if (extractedData && typeof extractedData === 'object') {
            // Check if it's in unified format and flatten relevant fields
            if (extractedData.client || extractedData.service_provider || extractedData.payment_terms) {
              flattenedData = {
                // Contract info
                contract_title: extractedData.contract_title,
                contract_type: extractedData.contract_type,
                invoice_date: extractedData.invoice_date,
                due_date: extractedData.due_date,
                
                // Client info (flattened from unified format)
                'client.name': extractedData.client?.name,
                'client.email': extractedData.client?.email,
                'client.address': extractedData.client?.address,
                'client.phone': extractedData.client?.phone,
                
                // Service provider info (flattened from unified format)
                'service_provider.name': extractedData.service_provider?.name,
                'service_provider.email': extractedData.service_provider?.email,
                'service_provider.address': extractedData.service_provider?.address,
                'service_provider.phone': extractedData.service_provider?.phone,
                
                // Payment terms (flattened from unified format)
                'payment_terms.amount': extractedData.payment_terms?.amount,
                'payment_terms.currency': extractedData.payment_terms?.currency,
                'payment_terms.due_days': extractedData.payment_terms?.due_days,
                'payment_terms.frequency': extractedData.payment_terms?.frequency,
                
                // Additional fields
                notes: extractedData.notes,
                special_terms: extractedData.special_terms,
                
                // Include any other top-level fields
                ...Object.fromEntries(
                  Object.entries(extractedData).filter(([key]) => 
                    !['client', 'service_provider', 'payment_terms', 'contract_title', 'contract_type', 
                      'invoice_date', 'due_date', 'notes', 'special_terms'].includes(key)
                  )
                )
              };
            }
          }
                               
          const validationIssues = validationData.validation_issues || [];
          const requiredFields = validationData.required_fields || [];
          
          console.log('📊 Extracted data:', extractedData);
          console.log('📊 Flattened data:', flattenedData);
          console.log('📊 Flattened data keys:', Object.keys(flattenedData));
          console.log('⚠️ Validation issues:', validationIssues);
          console.log('📝 Required fields:', requiredFields);
          
          // Combine validation issues and required fields
          const allValidationFields = [
            ...validationIssues.map((issue: any) => ({
              key: issue.field_name || issue.key || issue.field,
              value: issue.current_value || issue.value || flattenedData[issue.field_name || issue.key || issue.field] || '',
              requiresValidation: true,
              validationMessage: issue.issue_description || issue.message || issue.validation_message || 'This field requires validation',
              type: issue.field_type || issue.type || 'text',
              label: issue.field_label || issue.label || issue.field_name || issue.key || issue.field
            })),
            ...requiredFields.map((field: any) => ({
              key: field.field_name || field.key || field.name,
              value: field.current_value || field.value || flattenedData[field.field_name || field.key || field.name] || '',
              requiresValidation: true,
              validationMessage: field.description || field.message || 'This field is required',
              type: field.field_type || field.type || 'text',
              label: field.field_label || field.label || field.field_name || field.key || field.name
            }))
          ];
          
          const fieldsNeedingValidation = allValidationFields;
          
          console.log('🔧 Processed validation fields:', fieldsNeedingValidation);
          
          setInvoiceData(flattenedData);
          setValidationFields(fieldsNeedingValidation);
        } else {
          console.log('🔄 No navigation state data, fetching from API...');
          // Fallback: fetch from API using contractId
          await fetchDataFromAPI();
        }
      } catch (err) {
        setError('Failed to load validation data');
        console.error('❌ Error in initializeData:', err);
      } finally {
        setIsLoading(false);
      }
    };

    const fetchDataFromAPI = async () => {
      try {
        // Use contractId as workflowId for the API call
        const workflowIdToUse = contractId || 'unknown';
        setWorkflowId(workflowIdToUse);
        
        console.log('🔍 Fetching validation data for workflow:', workflowIdToUse);
        
        // Use the workflow service to fetch validation requirements
        const validationData = await workflowAPI.getValidationRequirements(workflowIdToUse);
        console.log('📋 Validation data received:', validationData);

        // Extract invoice data and validation fields from API response
        const extractedData = validationData.extracted_data || validationData.invoice_data || {};
        const fieldsNeedingValidation = validationData.fields_requiring_validation || validationData.validation_fields || [];
        
        // Set contract name from validation data if available
        setContractName(validationData.contract_name || validationData.document_name || 'Unknown Contract');

        setInvoiceData(extractedData);
        setValidationFields(fieldsNeedingValidation.map((field: any) => ({
          key: field.field_name || field.key,
          value: field.current_value || field.value || '',
          requiresValidation: true,
          validationMessage: field.issue_description || field.validation_message || 'This field requires validation',
          type: field.field_type || field.type || 'text',
          label: field.field_label || field.label || field.field_name || field.key
        })));

      } catch (error) {
        console.error('❌ Failed to fetch validation data:', error);
        
        // Fallback to mock data if API fails
        console.log('🔄 Using fallback mock data');
        const mockData = {
          // Basic Info
          invoiceNumber: 'INV-2024-001',
          invoiceDate: '2024-09-04',
          dueDate: '2024-10-04',
          
          // Client Info  
          clientName: 'ABC Corporation',
          clientEmail: 'billing@abc-corp.com',
          clientAddress: '123 Business Street, City, State 12345',
          
          // Service Details
          serviceDescription: 'Monthly Software License',
          quantity: 1,
          unitPrice: 2500.00,
          totalAmount: 2500.00,
          
          // Payment Terms
          paymentTerms: 'Net 30',
          currency: 'USD',
          taxRate: 0.08,
          taxAmount: 200.00,
          
          // Fields requiring validation
          projectReference: '', // Empty - needs validation
          billingPeriodStart: null, // Missing - needs validation  
          billingPeriodEnd: null, // Missing - needs validation
          additionalNotes: '', // Optional but flagged for review
          discountPercent: null, // Missing - needs validation
        };
        
        // Define which fields require validation
        const fieldsRequiringValidation = [
          {
            key: 'projectReference',
            value: mockData.projectReference,
            requiresValidation: true,
            validationMessage: 'Project reference number is required for proper billing tracking',
            type: 'text' as const,
            label: 'Project Reference'
          },
          {
            key: 'billingPeriodStart', 
            value: mockData.billingPeriodStart,
            requiresValidation: true,
            validationMessage: 'Billing period start date is required to determine service timeframe',
            type: 'date' as const,
            label: 'Billing Period Start'
          },
          {
            key: 'billingPeriodEnd',
            value: mockData.billingPeriodEnd, 
            requiresValidation: true,
            validationMessage: 'Billing period end date is required to determine service timeframe',
            type: 'date' as const,
            label: 'Billing Period End'
          },
          {
            key: 'discountPercent',
            value: mockData.discountPercent,
            requiresValidation: true,
            validationMessage: 'Please specify if any discount applies to this invoice',
            type: 'number' as const,
            label: 'Discount Percentage'
          },
          {
            key: 'additionalNotes',
            value: mockData.additionalNotes,
            requiresValidation: true,
            validationMessage: 'Add any special terms or notes for this invoice',
            type: 'textarea' as const,
            label: 'Additional Notes'
          }
        ];
        
        setInvoiceData(mockData);
        setValidationFields(fieldsRequiringValidation);
        setError('Failed to load validation data from server. Showing sample data.');
      }
    };

      initializeData();
    }, [contractId, location.state]);

  const handleFieldChange = (key: string, value: any) => {
    setInvoiceData(prev => ({
      ...prev,
      [key]: value
    }));
    
    // Update validation fields
    setValidationFields(prev => 
      prev.map(field => 
        field.key === key 
          ? { ...field, value: value }
          : field
      )
    );
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      // Convert flat field structure back to unified format for server
      const convertFlatToUnified = (flatData: Record<string, any>) => {
        const unified: Record<string, any> = {};
        
        for (const [key, value] of Object.entries(flatData)) {
          if (key.includes('.')) {
            // Handle nested paths (e.g., "client.name" -> {client: {name: value}})
            const keys = key.split('.');
            let current = unified;
            for (let i = 0; i < keys.length - 1; i++) {
              if (!current[keys[i]]) current[keys[i]] = {};
              current = current[keys[i]];
            }
            current[keys[keys.length - 1]] = value;
          } else {
            // Handle direct properties
            unified[key] = value;
          }
        }
        
        return unified;
      };

      // Prepare corrected data from validation fields
      const correctedDataFlat = validationFields.reduce((acc, field) => {
        acc[field.key] = field.value;
        return acc;
      }, {} as Record<string, any>);

      // Convert to unified format
      const correctedDataUnified = convertFlatToUnified(correctedDataFlat);
      
      console.log('📤 Submitting corrected data:', correctedDataUnified);
      
      // Prepare validation data for workflow resumption matching the expected format
      const resumeData = {
        workflow_id: workflowId || contractId,
        corrected_data: correctedDataUnified,
        user_notes: 'Human validation completed - fields corrected and verified'
      };
      
      // Use the workflow service to submit validation corrections
      const result = await workflowAPI.submitValidationCorrections(
        resumeData.workflow_id || '',
        resumeData.corrected_data,
        resumeData.user_notes
      );
      console.log('Workflow resumed successfully:', result);
      
      // Navigate back to contracts list or workflow status
      navigate('/contracts', { 
        state: { 
          message: 'Invoice data validated successfully. Workflow resumed.',
          type: 'success' 
        }
      });
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit validation');
      console.error('Validation submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getFieldType = (field: ValidationField): string => {
    if (field.type) return field.type;
    if (typeof field.value === 'number') return 'number';
    if (field.key.toLowerCase().includes('date')) return 'date';
    if (field.key.toLowerCase().includes('email')) return 'email';
    return 'text';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading invoice data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Button 
              variant="outline" 
              onClick={() => navigate('/contracts')}
              className="flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Contracts
            </Button>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Human Validation Required</h1>
          <div className="text-gray-600 mt-2 space-y-1">
            <p>
              Contract ID: <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">{contractId}</span>
            </p>
            {workflowId && (
              <p>
                Workflow ID: <span className="font-mono text-sm bg-blue-100 px-2 py-1 rounded">{workflowId}</span>
              </p>
            )}
            {contractName && (
              <p>
                Contract Name: <span className="font-medium">{contractName}</span>
              </p>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Extracted Invoice Data */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Extracted Invoice Data
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(invoiceData).map(([key, value]) => {
                const isValidationField = validationFields.some(f => f.key === key);
                return (
                  <div key={key} className="flex justify-between items-center py-2 border-b border-gray-100">
                    <div className="font-medium text-gray-700 capitalize">
                      {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-gray-900 text-sm">
                        {typeof value === 'object' && value !== null ? 
                          JSON.stringify(value) : 
                          (value || <span className="text-gray-400 italic">Not specified</span>)
                        }
                      </div>
                      {isValidationField && (
                        <Badge variant="warning" className="text-xs">
                          Needs Review
                        </Badge>
                      )}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Validation Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 18.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                Fields Requiring Validation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {validationFields.map((field) => (
                <div key={field.key} className="space-y-3">
                  <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex-shrink-0 w-5 h-5 bg-red-100 rounded-full flex items-center justify-center mt-0.5">
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-red-800">
                        {field.label || field.key}
                      </p>
                      <p className="text-sm text-red-600 mt-1">
                        {field.validationMessage}
                      </p>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {field.label || field.key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    </label>
                    
                    {field.type === 'textarea' ? (
                      <Textarea
                        value={field.value || ''}
                        onChange={(e) => handleFieldChange(field.key, e.target.value)}
                        placeholder={`Enter ${field.label?.toLowerCase() || field.key}`}
                        className="w-full"
                        rows={3}
                      />
                    ) : (
                      <Input
                        type={getFieldType(field)}
                        value={field.value || ''}
                        onChange={(e) => {
                          const value = field.type === 'number' 
                            ? (e.target.value ? parseFloat(e.target.value) : null)
                            : e.target.value;
                          handleFieldChange(field.key, value);
                        }}
                        placeholder={`Enter ${field.label?.toLowerCase() || field.key}`}
                        className="w-full"
                      />
                    )}
                  </div>
                </div>
              ))}
              
              <div className="pt-6 border-t border-gray-200">
                <Button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="w-full flex items-center justify-center gap-2"
                  variant="primary"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Submit Validation & Resume Workflow
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default InvoiceDataValidation;