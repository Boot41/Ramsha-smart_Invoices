import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button } from '../../components/ui';
import { AdaptiveInvoiceRenderer } from '../../components/invoices/AdaptiveInvoiceRenderer';
import ApiService, { type InvoiceDesign, type AdaptiveUIDesignsResponse } from '../../services/api';
import { ArrowLeft, Download, Share, Palette, RefreshCw } from 'lucide-react';

const InvoicePreviewPage: React.FC = () => {
  const { invoiceId } = useParams<{ invoiceId: string }>();
  const navigate = useNavigate();
  
  const [designs, setDesigns] = useState<InvoiceDesign[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [invoiceInfo, setInvoiceInfo] = useState<any>(null);

  const selectedDesign = designs[selectedIndex];

  useEffect(() => {
    if (!invoiceId) {
      setError('Invoice ID is required');
      setLoading(false);
      return;
    }

    fetchDesigns();
  }, [invoiceId]);

  const fetchDesigns = async () => {
    try {
      setLoading(true);
      setError(null);

      const response: AdaptiveUIDesignsResponse = await ApiService.getInvoiceDesigns(invoiceId!);
      
      if (response.designs && response.designs.length > 0) {
        setDesigns(response.designs);
        setInvoiceInfo({
          invoice_number: response.invoice_number,
          client_name: response.client_name,
          service_provider_name: response.service_provider_name,
          workflow_id: response.workflow_id
        });
        setSelectedIndex(0);
      } else {
        setError(response.message || 'No designs found for this invoice');
      }
    } catch (err) {
      console.error('Error fetching invoice designs:', err);
      setError('Failed to load invoice designs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDesignSelect = (index: number) => {
    setSelectedIndex(index);
  };

  const handleDownload = () => {
    // Implement download functionality
    console.log('Downloading invoice preview...');
  };

  const handleShare = () => {
    // Implement share functionality
    console.log('Sharing invoice preview...');
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/invoices')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Invoices
          </Button>
        </div>
        
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Loading invoice designs...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/invoices')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Invoices
          </Button>
        </div>
        
        <Card>
          <div className="p-8 text-center">
            <div className="text-red-500 mb-4">
              <Palette className="w-12 h-12 mx-auto opacity-50" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Unable to Load Designs
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchDesigns}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/invoices')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Invoices
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Invoice Preview</h1>
            {invoiceInfo && (
              <p className="text-gray-600">
                {invoiceInfo.invoice_number} • {invoiceInfo.client_name}
              </p>
            )}
          </div>
        </div>
        
        <div className="flex space-x-2">
          <Button variant="outline" onClick={handleShare}>
            <Share className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button onClick={handleDownload}>
            <Download className="w-4 h-4 mr-2" />
            Download PDF
          </Button>
        </div>
      </div>

      {/* Template Picker */}
      <Card>
        <div className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Palette className="w-5 h-5 mr-2" />
            Choose Design Template ({designs.length} available)
          </h3>
          
          <div className="flex flex-wrap gap-2">
            {designs.map((design, index) => (
              <Button
                key={design.design_id || index}
                variant={selectedIndex === index ? 'default' : 'outline'}
                onClick={() => handleDesignSelect(index)}
                className="flex-shrink-0"
              >
                {design.design_name}
                {design.style_theme && (
                  <span className="ml-2 text-xs text-gray-500 capitalize">
                    ({design.style_theme})
                  </span>
                )}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      {/* Invoice Preview */}
      <Card>
        <div className="p-6">
          {selectedDesign ? (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <AdaptiveInvoiceRenderer uiDefinition={selectedDesign} />
            </div>
          ) : (
            <div className="text-center py-12">
              <Palette className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Select a design template to preview</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default InvoicePreviewPage;