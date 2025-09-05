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
  const [naturalLanguageQuery, setNaturalLanguageQuery] = useState('');
  const [extractedFields, setExtractedFields] = useState<Record<string, any>>({});
  const [extractionConfidence, setExtractionConfidence] = useState(0);
  const [isExtractingFields, setIsExtractingFields] = useState(false);

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
          
          // Use the correct field names from ValidationRequirementsResponse
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
          console.log('⚠️ Validation issues:', validationIssues);
          console.log('📝 Required fields:', requiredFields);
          
          // Create validation fields from issues
          let allValidationFields: ValidationField[] = [];
          
          // Process validation issues
          if (validationIssues && validationIssues.length > 0) {
            console.log('Processing validation issues:', validationIssues);
            
            allValidationFields = validationIssues.map((issue: any) => {
              const fieldKey = issue.field_name || issue.key || issue.field;
              const currentValue = issue.current_value !== undefined 
                ? issue.current_value 
                : flattenedData[fieldKey];
              
              return {
                key: fieldKey,
                value: currentValue || '',
                requiresValidation: issue.requires_human_input !== false,
                validationMessage: issue.message || 'This field requires validation',
                type: getFieldTypeFromName(fieldKey),
                label: formatFieldLabel(fieldKey)
              };
            });
            
            console.log('🔧 Processed validation fields from issues:', allValidationFields);
          }
          
          // Add required fields that aren't already in validation issues
          if (requiredFields && requiredFields.length > 0) {
            const existingKeys = new Set(allValidationFields.map(f => f.key));
            
            const additionalFields = requiredFields
              .filter((field: any) => {
                const fieldKey = typeof field === 'string' ? field : (field.field_name || field.key || field.name);
                return fieldKey && !existingKeys.has(fieldKey);
              })
              .map((field: any) => {
                const fieldKey = typeof field === 'string' ? field : (field.field_name || field.key || field.name);
                return {
                  key: fieldKey,
                  value: flattenedData[fieldKey] || '',
                  requiresValidation: true,
                  validationMessage: typeof field === 'string' 
                    ? `This field is required: ${formatFieldLabel(fieldKey)}`
                    : (field.message || field.description || 'This field is required'),
                  type: getFieldTypeFromName(fieldKey),
                  label: formatFieldLabel(fieldKey)
                };
              });
              
            allValidationFields = [...allValidationFields, ...additionalFields];
          }
          
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
        const allValidationFields = validationIssues.map((issue: any) => {
          const fieldKey = issue.field_name || issue.key || issue.field;
          const currentValue = issue.current_value !== undefined 
            ? issue.current_value 
            : flattenedData[fieldKey];
          
          return {
            key: fieldKey,
            value: currentValue || '',
            requiresValidation: issue.requires_human_input !== false,
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

  const handleNaturalLanguageExtraction = async () => {
    if (!naturalLanguageQuery.trim()) {
      setError('Please enter a natural language query');
      return;
    }

    setIsExtractingFields(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/natural-language/extract-fields', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          query: naturalLanguageQuery,
          missing_fields: validationFields.map(f => f.key),
          current_invoice_data: invoiceData
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to extract fields: ${response.status}`);
      }

      const result = await response.json();
      console.log('🔍 Natural language extraction result:', result);

      if (result.success) {
        setExtractedFields(result.extracted_fields);
        setExtractionConfidence(result.confidence);
        
        // Update validation fields with extracted values
        setValidationFields(prev => 
          prev.map(field => ({
            ...field,
            value: result.extracted_fields[field.key] || field.value
          }))
        );
      } else {
        setError(result.message || 'Failed to extract fields from natural language query');
      }
    } catch (err) {
      console.error('❌ Natural language extraction error:', err);
      setError(err instanceof Error ? err.message : 'Failed to process natural language query');
    } finally {
      setIsExtractingFields(false);
    }
  };

  const handleSubmit = async (saveDirectly = false) => {
    if (!naturalLanguageQuery.trim()) {
      setError('Please enter a natural language description of the missing information');
      return;
    }

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
      
      // Prepare validation data for workflow resumption using natural language
      const resumeData = {
        workflow_id: activeWorkflowId || currentId,
        natural_language_query: naturalLanguageQuery,
        user_notes: saveDirectly 
          ? 'Human validation completed using natural language - saved directly to database' 
          : 'Human validation completed using natural language query - AI extracted fields and verified'
      };
      
      if (saveDirectly) {
        // Use the new direct save API endpoint
        console.log('💾 Using direct save endpoint (skipping correction agent)');
        const response = await fetch(`http://localhost:8000/api/v1/validation/save-direct`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify(resumeData)
        });

        if (!response.ok) {
          throw new Error(`Failed to save invoice data directly: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ Invoice data saved directly:', result);
        
        // Navigate with success message
        navigate('/invoices', { 
          state: { 
            message: `Invoice saved successfully! Invoice ID: ${result.invoice_id}`,
            type: 'success',
            invoiceId: result.invoice_id
          }
        });
        return;
      }
      
      // For workflow-based validation, use the updated validation resume endpoint
      if (activeWorkflowId && activeWorkflowId !== currentId) {
        // This came from the workflow tracker, use validation resume API with natural language support
        const response = await fetch(`http://localhost:8000/api/v1/validation/resume`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({
            workflow_id: activeWorkflowId,
            natural_language_query: naturalLanguageQuery,
            user_notes: resumeData.user_notes
          })
        });

        if (!response.ok) {
          throw new Error(`Failed to submit validation: ${response.status}`);
        }

        const result = await response.json();
        console.log('Workflow validation submitted successfully:', result);
      } else {
        // Use the updated validation resume endpoint for backwards compatibility
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
        console.log('Workflow resumed successfully:', result);
      }
      
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

          {/* Natural Language Validation */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10m0 0V6a2 2 0 00-2-2H9a2 2 0 00-2 2v2m0 0v10a2 2 0 002 2h10a2 2 0 002-2V8M9 12h6" />
                </svg>
                Natural Language Validation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Missing Fields Summary */}
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-yellow-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-yellow-800 mb-2">Missing Information</h3>
                    <p className="text-sm text-yellow-700 mb-3">
                      The following fields need validation. Instead of filling out forms, describe the missing information in natural language below:
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {validationFields.map((field) => (
                        <div key={field.key} className="text-xs text-yellow-700 bg-yellow-100 px-2 py-1 rounded">
                          • {field.label || formatFieldLabel(field.key)}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Natural Language Input */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📝 Describe the missing information in natural language:
                  </label>
                  <Textarea
                    value={naturalLanguageQuery}
                    onChange={(e) => setNaturalLanguageQuery(e.target.value)}
                    placeholder='Example: "The client is John Smith from john@company.com and the service provider is TechCorp LLC. The monthly fee is $1500 for web development services starting January 2025."'
                    className="w-full"
                    rows={5}
                  />
                </div>
                
                <div className="flex gap-2">
                  <Button
                    onClick={handleNaturalLanguageExtraction}
                    disabled={isExtractingFields || !naturalLanguageQuery.trim()}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    {isExtractingFields ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        Extracting...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        Preview Fields
                      </>
                    )}
                  </Button>
                  
                  {Object.keys(extractedFields).length > 0 && (
                    <div className="flex items-center gap-2 text-sm">
                      <Badge variant="success" className="text-xs">
                        ✓ {Object.keys(extractedFields).length} fields extracted
                      </Badge>
                      <span className="text-gray-600">
                        {Math.round(extractionConfidence * 100)}% confidence
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Extracted Fields Preview */}
                {Object.keys(extractedFields).length > 0 && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="text-sm font-medium text-blue-800 mb-3">🔍 Preview of Extracted Fields:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(extractedFields).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center text-sm bg-white p-2 rounded border">
                          <span className="text-gray-600 font-medium">{formatFieldLabel(key)}:</span>
                          <span className="text-blue-900 font-semibold">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Examples */}
                <div className="text-xs text-gray-600 bg-gray-50 p-4 rounded-lg">
                  <p className="font-medium mb-2">💡 Examples that work well:</p>
                  <ul className="space-y-1 ml-4">
                    <li>• "Client: John Smith, Provider: ABC Corp, Amount: $2000, Service: Consulting services"</li>
                    <li>• "The invoice is for Sarah from TechCorp for $800 monthly maintenance services"</li>
                    <li>• "Client is Ramsha, provider is Iqbal, amount is $1200 for web development work"</li>
                    <li>• "Invoice for David Brown (david@company.com) from WebDev Pro LLC for $950 quarterly website maintenance"</li>
                  </ul>
                </div>
              </div>
              
              <div className="pt-6 border-t border-gray-200 space-y-3">
                {/* Direct Save Button */}
                <Button
                  onClick={() => handleSubmit(true)}
                  disabled={isSubmitting || !naturalLanguageQuery.trim()}
                  className="w-full flex items-center justify-center gap-2"
                  variant="primary"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                      </svg>
                      💾 Save with Natural Language
                    </>
                  )}
                </Button>
                
                <p className="text-sm text-gray-600 text-center">
                  AI extracts fields from your description and saves directly to database
                </p>
                
                {/* Workflow Resume Button */}
                <Button
                  onClick={() => handleSubmit(false)}
                  disabled={isSubmitting || !naturalLanguageQuery.trim()}
                  className="w-full flex items-center justify-center gap-2"
                  variant="secondary"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      🚀 Submit & Resume Full Workflow
                    </>
                  )}
                </Button>
                
                <p className="text-sm text-gray-500 text-center">
                  AI extracts fields, continues through correction agent, invoice generation, and creates HTML invoice
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