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
  const { contractId, workflowId } = useParams<{ contractId?: string; workflowId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Use workflowId if available, otherwise fallback to contractId
  const currentId = workflowId || contractId;
  
  const [invoiceData, setInvoiceData] = useState<InvoiceData>({});
  const [validationFields, setValidationFields] = useState<ValidationField[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const [contractName, setContractName] = useState<string>('');

  // Get data from navigation state or fetch from API
  useEffect(() => {
    const initializeData = async () => {
      console.log('🚀 InvoiceDataValidation component initializing...');
      console.log('📍 Current ID:', currentId);
      console.log('📍 Location state:', location.state);
      
      setIsLoading(true);
      try {
        // Get data from navigation state if available
        const navigationState = location.state as any;
        
        if (navigationState?.validationData) {
          console.log('✅ Using navigation state data');
          // Use data passed from workflow
          const { validationData, workflowId: navWorkflowId, contractName: navContractName, workflowStatus } = navigationState;
          
          setActiveWorkflowId(navWorkflowId);
          setContractName(navContractName || '');
          
          // Extract invoice data and validation fields from workflow data
          console.log('📋 Full validation data:', validationData);
          console.log('🔍 Available keys in validation data:', Object.keys(validationData));
          
          // Extract invoice data and required field updates from new backend format
          const extractedData = validationData.current_data || 
                               validationData.extracted_data || 
                               validationData.invoice_data || 
                               {};
          
          // Flatten nested objects for display, handling null values properly
          const flattenData = (obj: any, prefix = ''): Record<string, any> => {
            const result: Record<string, any> = {};
            
            if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
              for (const [key, value] of Object.entries(obj)) {
                const newKey = prefix ? `${prefix}.${key}` : key;
                
                if (value && typeof value === 'object' && !Array.isArray(value)) {
                  // For nested objects, flatten recursively
                  Object.assign(result, flattenData(value, newKey));
                } else {
                  // For primitive values, arrays, or null, store directly
                  result[newKey] = value;
                }
              }
            }
            
            return result;
          };
          
          const flattenedData = flattenData(extractedData);
          
          // Process validation issues from the new backend format
          const validationIssues = validationData.validation_issues || [];
          const requiredFields = validationData.required_fields || [];
          
          console.log('📊 Extracted data:', extractedData);
          console.log('📊 Flattened data:', flattenedData);
          console.log('📊 Flattened data keys:', Object.keys(flattenedData));
          console.log('📝 Validation issues:', validationIssues);
          console.log('📝 Required fields:', requiredFields);
          
          // Create validation fields from validation issues that require human input
          const allValidationFields: ValidationField[] = validationIssues
            .filter((issue: any) => issue.requires_human_input)
            .map((issue: any) => {
              const fieldKey = issue.field_name;
              const currentValue = issue.current_value !== undefined 
                ? issue.current_value 
                : flattenedData[fieldKey];
              
              return {
                key: fieldKey,
                value: currentValue || issue.suggested_value || '',
                requiresValidation: issue.severity === 'error',
                validationMessage: issue.message || 'This field requires validation',
                type: getFieldTypeFromName(fieldKey),
                label: formatFieldLabel(fieldKey)
              };
            });
          
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
        // Use currentId as workflowId for the API call
        const workflowIdToUse = currentId || 'unknown';
        setActiveWorkflowId(workflowIdToUse);
        
        console.log('🔍 Fetching validation data for workflow:', workflowIdToUse);
        
        // Use the workflow service to fetch validation requirements
        const validationData = await workflowAPI.getValidationRequirements(workflowIdToUse);
        console.log('📋 Validation data received:', validationData);

        // Set contract name from validation data if available
        setContractName(validationData.contract_name || validationData.document_name || 'Unknown Contract');

        // Extract invoice data and handle flattening the same way as navigation state
        const extractedData = validationData.current_data || validationData.extracted_data || validationData.invoice_data || {};
        
        // Flatten nested objects for display
        const flattenData = (obj: any, prefix = ''): Record<string, any> => {
          const result: Record<string, any> = {};
          
          if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
            for (const [key, value] of Object.entries(obj)) {
              const newKey = prefix ? `${prefix}.${key}` : key;
              
              if (value && typeof value === 'object' && !Array.isArray(value)) {
                Object.assign(result, flattenData(value, newKey));
              } else {
                result[newKey] = value;
              }
            }
          }
          
          return result;
        };
        
        const flattenedData = flattenData(extractedData);
        
        // Process validation issues the same way as navigation state
        const validationIssues = validationData.validation_issues || [];
        const requiredFields = validationData.required_fields || [];
        
        console.log('📝 API Validation issues:', validationIssues);
        console.log('📝 API Required fields:', requiredFields);
        
        // Create validation fields from validation issues that require human input
        const allValidationFields = validationIssues
          .filter((issue: any) => issue.requires_human_input)
          .map((issue: any) => {
            const fieldKey = issue.field_name;
            const currentValue = issue.current_value !== undefined 
              ? issue.current_value 
              : flattenedData[fieldKey];
            
            return {
              key: fieldKey,
              value: currentValue || issue.suggested_value || '',
              requiresValidation: issue.severity === 'error',
              validationMessage: issue.message || 'This field requires validation',
              type: getFieldTypeFromName(fieldKey),
              label: formatFieldLabel(fieldKey)
            };
          });

        setInvoiceData(flattenedData);
        setValidationFields(allValidationFields);

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
    }, [currentId, location.state]);

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
    // Validate that all required fields have values
    const emptyRequiredFields = validationFields.filter(field => 
      field.requiresValidation && (!field.value || field.value.toString().trim() === '')
    );
    
    if (emptyRequiredFields.length > 0) {
      setError(`Please fill in all required fields: ${emptyRequiredFields.map(f => f.label).join(', ')}`);
      return;
    }

    setIsSubmitting(true);
    setError(null);
    
    try {
      // Prepare field values in the exact format expected by backend
      const fieldValues = validationFields.reduce((acc, field) => {
        acc[field.key] = field.value;
        return acc;
      }, {} as Record<string, any>);
      
      console.log('📤 Submitting field values:', fieldValues);
      
      // Prepare validation data for workflow resumption using corrected_data format
      const resumeData = {
        workflow_id: activeWorkflowId || currentId,
        corrected_data: fieldValues,
        user_notes: "Validation completed via frontend form"
      };
      
      // Use the validation resume endpoint with structured field values
      const response = await fetch(`http://localhost:8000/api/v1/validation/resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(resumeData)
      });

      if (!response.ok) {
        throw new Error(`Failed to submit validation: ${response.status}`);
      }

      const result = await response.json();
      console.log('✅ Validation submitted successfully with structured field values:', result);
      
      // Navigate back to workflow tracker if came from workflow, otherwise to contracts
      if (activeWorkflowId && activeWorkflowId !== currentId) {
        navigate(`/workflow/${activeWorkflowId}`, { 
          state: { 
            message: 'Invoice data validated successfully. Workflow resumed.',
            type: 'success',
            contractName: contractName
          }
        });
      } else {
        navigate('/contracts', { 
          state: { 
            message: 'Invoice data validated successfully. Workflow resumed.',
            type: 'success' 
          }
        });
      }
      
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

  const getFieldTypeFromName = (fieldName: string): string => {
    if (!fieldName) return 'text';
    const lower = fieldName.toLowerCase();
    if (lower.includes('date')) return 'date';
    if (lower.includes('email')) return 'email';
    if (lower.includes('amount') || lower.includes('price') || lower.includes('cost')) return 'number';
    if (lower.includes('phone')) return 'tel';
    return 'text';
  };

  const formatFieldLabel = (fieldName: string): string => {
    if (!fieldName) return 'Unknown Field';
    
    // Handle dotted notation (e.g., "payment_terms.amount" -> "Payment Terms Amount")
    const parts = fieldName.split('.');
    const formattedParts = parts.map(part => 
      part.replace(/([A-Z])/g, ' $1')
          .replace(/_/g, ' ')
          .replace(/\b\w/g, l => l.toUpperCase())
          .trim()
    );
    
    return formattedParts.join(' ');
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
              onClick={() => {
                if (activeWorkflowId && activeWorkflowId !== currentId) {
                  navigate(`/workflow/${activeWorkflowId}`, { state: { contractName } });
                } else {
                  navigate('/contracts');
                }
              }}
              className="flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              {activeWorkflowId && activeWorkflowId !== currentId ? 'Back to Workflow' : 'Back to Contracts'}
            </Button>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Human Validation Required</h1>
          <div className="text-gray-600 mt-2 space-y-1">
            <p>
              Current ID: <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">{currentId}</span>
            </p>
            {activeWorkflowId && (
              <p>
                Workflow ID: <span className="font-mono text-sm bg-blue-100 px-2 py-1 rounded">{activeWorkflowId}</span>
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

          {/* Field Validation Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
                Field Validation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Fields Summary */}
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-yellow-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-yellow-800 mb-2">Fields Requiring Validation</h3>
                    <p className="text-sm text-yellow-700">
                      Please review and update the following fields to complete the invoice validation:
                    </p>
                  </div>
                </div>
              </div>

              {/* Validation Fields */}
              <div className="space-y-4">
                {validationFields.map((field) => (
                  <div key={field.key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="block text-sm font-medium text-gray-700">
                        {field.label || formatFieldLabel(field.key)}
                        {field.requiresValidation && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      <Badge variant={field.requiresValidation ? "warning" : "secondary"} className="text-xs">
                        {field.requiresValidation ? "Required" : "Optional"}
                      </Badge>
                    </div>
                    
                    {field.validationMessage && (
                      <p className="text-sm text-gray-600 mb-2">
                        {field.validationMessage}
                      </p>
                    )}
                    
                    {field.type === 'textarea' ? (
                      <Textarea
                        value={field.value || ''}
                        onChange={(e) => handleFieldChange(field.key, e.target.value)}
                        placeholder={`Enter ${field.label || formatFieldLabel(field.key)}`}
                        className="w-full"
                        rows={3}
                      />
                    ) : (
                      <Input
                        type={getFieldType(field)}
                        value={field.value || ''}
                        onChange={(e) => {
                          const value = field.type === 'number' ? parseFloat(e.target.value) || e.target.value : e.target.value;
                          handleFieldChange(field.key, value);
                        }}
                        placeholder={`Enter ${field.label || formatFieldLabel(field.key)}`}
                        className="w-full"
                      />
                    )}
                  </div>
                ))}
              </div>
              
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
                      Submit Validation & Continue Workflow
                    </>
                  )}
                </Button>
                
                <p className="text-sm text-gray-500 text-center mt-3">
                  Submit the corrected field values to continue the invoice processing workflow
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default InvoiceDataValidation;