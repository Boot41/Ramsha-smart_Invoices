import React, { useState, useEffect, useRef } from 'react';
import DOMPurify from 'dompurify';

interface InvoicePreviewProps {
  templateId: string;
  templateName: string;
  invoiceData?: any;
  invoiceNumber?: string;
  invoiceDate?: Date;
  dueDate?: Date;
  status?: string;
  scale?: number;
  showControls?: boolean;
}

interface PreviewControls {
  zoom: number;
  showPrintPreview: boolean;
}

const InvoicePreview: React.FC<InvoicePreviewProps> = ({ 
  templateId, 
  templateName,
  invoiceData,
  invoiceNumber,
  invoiceDate,
  dueDate,
  status = "Draft",
  scale = 0.75,
  showControls = true
}) => {
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [controls, setControls] = useState<PreviewControls>({
    zoom: scale,
    showPrintPreview: false
  });
  
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadInvoicePreview();
  }, [templateId, invoiceData, invoiceNumber, invoiceDate, dueDate, status]);

  const loadInvoicePreview = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/templates/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          templateId,
          invoiceData: invoiceData || await createSampleInvoiceData(templateId),
          invoiceNumber: invoiceNumber || `PREVIEW-${Date.now().toString().slice(-6)}`,
          invoiceDate: invoiceDate?.toISOString() || new Date().toISOString(),
          dueDate: dueDate?.toISOString() || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          status
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to load invoice preview: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Sanitize HTML content using DOMPurify
      const sanitizedHtml = DOMPurify.sanitize(data.html, {
        ALLOWED_TAGS: [
          'html', 'head', 'title', 'meta', 'style', 'body',
          'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'table', 'thead', 'tbody', 'tr', 'th', 'td',
          'ul', 'ol', 'li', 'br', 'hr', 'strong', 'b', 'em', 'i'
        ],
        ALLOWED_ATTR: [
          'class', 'id', 'style', 'colspan', 'rowspan'
        ],
        FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input', 'button'],
        FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur']
      });

      setHtmlContent(sanitizedHtml);
      
    } catch (err) {
      console.error('Error loading invoice preview:', err);
      setError(err instanceof Error ? err.message : 'Failed to load invoice preview');
    } finally {
      setLoading(false);
    }
  };

  const createSampleInvoiceData = async (_templateId: string) => {
    // Create sample data for preview
    return {
      contract_title: "Professional Services Agreement",
      client: {
        name: "Demo Client Inc.",
        email: "demo@client.com",
        address: "123 Business Ave\nCorporate City, CC 12345",
        phone: "+1 (555) 123-4567"
      },
      service_provider: {
        name: "Your Company Name",
        email: "info@yourcompany.com",
        address: "456 Service St\nProvider City, PC 67890", 
        phone: "+1 (555) 987-6543"
      },
      payment_terms: {
        amount: 2500.00,
        currency: "USD",
        frequency: "monthly"
      },
      services: [
        {
          description: "Consulting Services",
          quantity: 20,
          unit_price: 75.00,
          total_amount: 1500.00
        },
        {
          description: "Implementation Services",
          quantity: 10,
          unit_price: 100.00,
          total_amount: 1000.00
        }
      ]
    };
  };

  const handleZoomChange = (newZoom: number) => {
    setControls(prev => ({ ...prev, zoom: newZoom }));
  };

  const handlePrintPreview = () => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.print();
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await fetch('/api/templates/generate-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          templateId,
          invoiceData: invoiceData || await createSampleInvoiceData(templateId),
          invoiceNumber: invoiceNumber || `INV-${Date.now().toString().slice(-6)}`,
          invoiceDate: invoiceDate?.toISOString() || new Date().toISOString(),
          dueDate: dueDate?.toISOString() || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          status: status === "Draft" ? "Pending" : status
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate PDF');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${invoiceNumber || 'preview'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
    } catch (err) {
      console.error('Error generating PDF:', err);
      alert('Failed to generate PDF. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <span className="text-sm text-gray-600">Loading invoice preview...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-red-50 rounded-lg border border-red-200">
        <div className="text-center">
          <div className="text-red-400 text-2xl mb-2">⚠️</div>
          <p className="text-sm text-red-600 mb-2">{error}</p>
          <button 
            onClick={loadInvoicePreview}
            className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
      {showControls && (
        <div className="flex items-center justify-between p-3 border-b bg-gray-50">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-600">Zoom:</label>
              <select 
                value={controls.zoom} 
                onChange={(e) => handleZoomChange(parseFloat(e.target.value))}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value={0.5}>50%</option>
                <option value={0.75}>75%</option>
                <option value={1.0}>100%</option>
                <option value={1.25}>125%</option>
                <option value={1.5}>150%</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                status === 'Draft' ? 'bg-gray-100 text-gray-800' :
                status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
                status === 'Paid' ? 'bg-green-100 text-green-800' :
                status === 'Overdue' ? 'bg-red-100 text-red-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {status}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrintPreview}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center space-x-1"
            >
              <span>🖨️</span>
              <span>Print</span>
            </button>
            <button
              onClick={handleDownloadPDF}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 flex items-center space-x-1"
            >
              <span>📄</span>
              <span>PDF</span>
            </button>
          </div>
        </div>
      )}

      <div 
        ref={containerRef}
        className="invoice-preview-container"
        style={{ 
          transform: `scale(${controls.zoom})`,
          transformOrigin: 'top left',
          width: `${100 / controls.zoom}%`,
          height: 'auto',
          overflow: 'hidden'
        }}
      >
        <iframe
          ref={iframeRef}
          srcDoc={htmlContent}
          className="w-full border-0"
          style={{ 
            height: '800px',
            minHeight: '600px'
          }}
          sandbox="allow-same-origin allow-scripts"
          title={`Invoice Preview - ${templateName}`}
        />
      </div>
    </div>
  );
};

export default InvoicePreview;