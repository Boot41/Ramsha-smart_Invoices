import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { mockRentInvoiceTemplates, mockRentalAgreements } from '../../data/mockData';
import type { RentInvoiceTemplate, RentalAgreement, SelectOption } from '../../../types';

const InvoiceTemplates: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [templates] = useState<RentInvoiceTemplate[]>(mockRentInvoiceTemplates);
  const [selectedAgreement, setSelectedAgreement] = useState<string>('');
  const [previewTemplate, setPreviewTemplate] = useState<RentInvoiceTemplate | null>(null);
  const [currentAgreement, setCurrentAgreement] = useState<RentalAgreement | null>(null);

  useEffect(() => {
    // Check if we received a selected agreement from navigation state
    if (location.state?.selectedAgreement) {
      const agreement = location.state.selectedAgreement as RentalAgreement;
      setCurrentAgreement(agreement);
      setSelectedAgreement(agreement.id);
    }
  }, [location.state]);

  const agreementOptions: SelectOption[] = mockRentalAgreements.map(agreement => ({
    value: agreement.id,
    label: `${agreement.propertyTitle} - ${agreement.tenantName}`
  }));

  const getPropertyTypeColor = (type: string) => {
    switch (type) {
      case 'apartment': return 'bg-blue-100 text-blue-800';
      case 'house': return 'bg-green-100 text-green-800';
      case 'commercial': return 'bg-purple-100 text-purple-800';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  const handleUseTemplate = (template: RentInvoiceTemplate) => {
    if (!selectedAgreement) {
      alert('Please select a rental agreement first');
      return;
    }

    const agreement = mockRentalAgreements.find(a => a.id === selectedAgreement);
    if (agreement) {
      // Navigate to invoice scheduling with both selected agreement and template
      navigate('/invoices/scheduling', {
        state: { 
          selectedAgreement: agreement,
          selectedTemplate: template
        }
      });
    }
  };

  const generatePreviewInvoice = (template: RentInvoiceTemplate, agreement?: RentalAgreement) => {
    const mockAgreement = agreement || mockRentalAgreements[0];
    const currentDate = new Date();
    const nextMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1);
    
    return {
      ...template.template,
      invoiceNumber: `RENT-${currentDate.getFullYear()}-${String(currentDate.getMonth() + 2).padStart(3, '0')}`,
      tenantName: mockAgreement.tenantName,
      tenantEmail: mockAgreement.tenantEmail,
      propertyAddress: {
        street: mockAgreement.propertyAddress,
        city: '',
        state: '',
        zipCode: '',
        country: 'USA'
      },
      monthlyRent: mockAgreement.monthlyRent,
      dueDate: nextMonth.toISOString().split('T')[0],
      issueDate: new Date().toISOString().split('T')[0],
      rentPeriod: {
        startDate: nextMonth.toISOString().split('T')[0],
        endDate: new Date(nextMonth.getFullYear(), nextMonth.getMonth() + 1, 0).toISOString().split('T')[0]
      },
      totalAmount: mockAgreement.monthlyRent + (template.template.items?.reduce((sum, item) => sum + (item.amount || 0), 0) || 0)
    };
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Invoice Templates</h1>
          <p className="text-slate-600 mt-2">Choose a template to generate rent invoices</p>
        </div>
        <Button variant="outline">Create New Template</Button>
      </div>

      {/* Agreement Selection */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Select Rental Agreement</CardTitle>
          <CardDescription className="text-blue-700">
            Choose which property and tenant to generate the invoice for
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            options={[{ value: '', label: 'Select a rental agreement...' }, ...agreementOptions]}
            value={selectedAgreement}
            onChange={setSelectedAgreement}
            placeholder="Choose rental agreement"
          />
          {selectedAgreement && (
            <div className="mt-4 p-4 bg-white rounded-lg border">
              {(() => {
                const agreement = mockRentalAgreements.find(a => a.id === selectedAgreement);
                return agreement ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-slate-900">{agreement.propertyTitle}</h4>
                      <p className="text-sm text-slate-600">{agreement.propertyAddress}</p>
                      <p className="text-sm text-slate-600">Tenant: {agreement.tenantName}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-slate-900">${agreement.monthlyRent.toLocaleString()}/month</p>
                      <Badge variant="success">{agreement.status}</Badge>
                    </div>
                  </div>
                ) : null;
              })()}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <Card key={template.id} className="relative hover:shadow-lg transition-all duration-200">
            {template.isDefault && (
              <div className="absolute -top-2 -right-2">
                <Badge variant="warning" size="sm">Default</Badge>
              </div>
            )}
            
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{template.name}</span>
                <Badge 
                  className={`${getPropertyTypeColor(template.propertyType)} capitalize`}
                  variant="secondary"
                >
                  {template.propertyType}
                </Badge>
              </CardTitle>
              <CardDescription>{template.description}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Template Preview */}
              <div className="bg-slate-50 p-4 rounded-lg border-2 border-dashed border-slate-200">
                <h5 className="font-semibold text-slate-700 mb-2">Invoice Items:</h5>
                <div className="space-y-2">
                  {template.template.items?.map((item, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-slate-600">{item.description}</span>
                      <span className="font-medium text-slate-900">
                        {item.amount > 0 ? `$${item.amount}` : 'Variable'}
                      </span>
                    </div>
                  ))}
                </div>
                {template.template.notes && (
                  <div className="mt-3 pt-3 border-t border-slate-200">
                    <p className="text-xs text-slate-500">{template.template.notes}</p>
                  </div>
                )}
              </div>

              {/* Template Stats */}
              <div className="flex justify-between text-sm text-slate-600">
                <span>Created: {new Date(template.createdAt).toLocaleDateString()}</span>
                <span>Modified: {new Date(template.updatedAt).toLocaleDateString()}</span>
              </div>
            </CardContent>

            <CardFooter className="flex space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setPreviewTemplate(template)}
                fullWidth
              >
                Preview
              </Button>
              <Button 
                variant="primary" 
                size="sm"
                onClick={() => handleUseTemplate(template)}
                disabled={!selectedAgreement}
                fullWidth
              >
                Use Template
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {/* Add New Template Card */}
      <Card className="border-2 border-dashed border-slate-300 hover:border-blue-400 hover:bg-blue-50 transition-all duration-200">
        <CardContent className="py-12 text-center">
          <svg className="w-12 h-12 text-slate-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <h3 className="text-lg font-semibold text-slate-700 mb-2">Create Custom Template</h3>
          <p className="text-slate-600 mb-4">Design your own invoice template with custom fields and branding</p>
          <Button variant="outline">Create Template</Button>
        </CardContent>
      </Card>

      {/* Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Invoice Preview - {previewTemplate.name}</CardTitle>
                  <CardDescription>Preview how the invoice will look</CardDescription>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setPreviewTemplate(null)}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </Button>
              </div>
            </CardHeader>

            <CardContent>
              {(() => {
                const agreement = selectedAgreement ? 
                  mockRentalAgreements.find(a => a.id === selectedAgreement) : 
                  mockRentalAgreements[0];
                const previewInvoice = generatePreviewInvoice(previewTemplate, agreement);

                return (
                  <div className="bg-white border rounded-lg p-8">
                    {/* Invoice Header */}
                    <div className="flex justify-between items-start mb-8">
                      <div>
                        <h2 className="text-2xl font-bold text-slate-900">RENT INVOICE</h2>
                        <p className="text-slate-600">Invoice #{previewInvoice.invoiceNumber}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-600">Issue Date: {previewInvoice.issueDate}</p>
                        <p className="text-sm text-slate-600">Due Date: {previewInvoice.dueDate}</p>
                      </div>
                    </div>

                    {/* Tenant and Property Info */}
                    <div className="grid grid-cols-2 gap-8 mb-8">
                      <div>
                        <h3 className="font-semibold text-slate-900 mb-2">Bill To:</h3>
                        <p className="text-slate-700">{previewInvoice.tenantName}</p>
                        <p className="text-slate-600">{previewInvoice.tenantEmail}</p>
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900 mb-2">Property:</h3>
                        <p className="text-slate-700">{previewInvoice.propertyAddress?.street}</p>
                      </div>
                    </div>

                    {/* Invoice Items */}
                    <div className="border-t border-b border-slate-200 py-4 mb-6">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-slate-100">
                            <th className="text-left py-2 font-semibold text-slate-900">Description</th>
                            <th className="text-right py-2 font-semibold text-slate-900">Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {previewTemplate.template.items?.map((item, index) => (
                            <tr key={index}>
                              <td className="py-2 text-slate-700">{item.description}</td>
                              <td className="py-2 text-right text-slate-900">
                                ${(item.amount || previewInvoice.monthlyRent || 0).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Total */}
                    <div className="flex justify-end mb-6">
                      <div className="w-64">
                        <div className="flex justify-between py-2 text-lg font-bold text-slate-900">
                          <span>Total Due:</span>
                          <span>${previewInvoice.totalAmount?.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                    {/* Notes */}
                    {previewTemplate.template.notes && (
                      <div className="bg-slate-50 p-4 rounded-lg">
                        <h4 className="font-semibold text-slate-900 mb-2">Payment Instructions:</h4>
                        <p className="text-slate-700 text-sm">{previewTemplate.template.notes}</p>
                      </div>
                    )}
                  </div>
                );
              })()}
            </CardContent>

            <CardFooter className="flex space-x-3">
              <Button variant="outline" onClick={() => setPreviewTemplate(null)}>
                Close Preview
              </Button>
              <Button 
                variant="primary" 
                onClick={() => {
                  handleUseTemplate(previewTemplate);
                  setPreviewTemplate(null);
                }}
                disabled={!selectedAgreement}
              >
                Use This Template
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  );
};

export default InvoiceTemplates;