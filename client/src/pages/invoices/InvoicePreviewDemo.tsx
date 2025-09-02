import React, { useState, useEffect } from 'react';
import InvoicePreview from '../../components/InvoicePreview';

const InvoicePreviewDemo: React.FC = () => {
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/templates/');
      
      if (!response.ok) {
        throw new Error('Failed to load templates');
      }

      const data = await response.json();
      setTemplates(data.templates || []);
      
      if (data.templates && data.templates.length > 0) {
        setSelectedTemplate(data.templates[0].id);
      }
      
    } catch (err) {
      console.error('Error loading templates:', err);
      setError(err instanceof Error ? err.message : 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading templates...</p>
        </div>
      </div>
    );
  }

  if (error || templates.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
          <div className="text-red-400 text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">No Templates Available</h2>
          <p className="text-gray-600 mb-4">
            {error || 'No invoice templates found. Please generate some templates first.'}
          </p>
          <button
            onClick={() => window.location.href = '/invoices'}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go to Invoice Management
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Invoice Preview System
          </h1>
          <p className="text-gray-600">
            Secure HTML template rendering with AI-generated invoice designs
          </p>
        </div>

        {/* Template Selector */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">
              Template Selection
            </h2>
            <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2 py-1 rounded-full">
              {templates.length} Available
            </span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div
                key={template.id}
                className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                  selectedTemplate === template.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedTemplate(template.id)}
              >
                <h3 className="font-medium text-gray-800 mb-2">{template.name}</h3>
                <p className="text-sm text-gray-600 mb-2">{template.type}</p>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Model: {template.model_used}</span>
                  <span>{new Date(template.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Features Overview */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Security Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-green-600 text-2xl mb-2">🛡️</div>
              <h3 className="font-medium text-gray-800">HTML Sanitization</h3>
              <p className="text-sm text-gray-600">DOMPurify + server-side cleaning</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-blue-600 text-2xl mb-2">🔒</div>
              <h3 className="font-medium text-gray-800">Sandbox Rendering</h3>
              <p className="text-sm text-gray-600">Isolated iframe execution</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-purple-600 text-2xl mb-2">🎯</div>
              <h3 className="font-medium text-gray-800">Dynamic Injection</h3>
              <p className="text-sm text-gray-600">Safe placeholder replacement</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-orange-600 text-2xl mb-2">📄</div>
              <h3 className="font-medium text-gray-800">PDF Generation</h3>
              <p className="text-sm text-gray-600">WeasyPrint HTML to PDF</p>
            </div>
          </div>
        </div>

        {/* Invoice Preview */}
        {selectedTemplate && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-800">Live Preview</h2>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Template:</span>
                <code className="bg-gray-100 px-2 py-1 rounded text-sm">{selectedTemplate}</code>
              </div>
            </div>
            
            <InvoicePreview
              templateId={selectedTemplate}
              templateName={templates.find(t => t.id === selectedTemplate)?.name || 'Template'}
              invoiceNumber={`DEMO-${Date.now().toString().slice(-6)}`}
              invoiceDate={new Date()}
              dueDate={new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)}
              status="Draft"
              scale={0.8}
              showControls={true}
            />
          </div>
        )}

        {/* Usage Instructions */}
        <div className="bg-gray-900 text-white rounded-lg p-6 mt-8">
          <h2 className="text-xl font-semibold mb-4">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-2">1. AI Template Generation</h3>
              <p className="text-gray-300 text-sm mb-4">
                Gemini 2.0 Flash generates secure HTML/CSS templates with placeholders
              </p>
              
              <h3 className="font-semibold mb-2">2. Secure Rendering</h3>
              <p className="text-gray-300 text-sm">
                Templates are sanitized and rendered in isolated sandboxed containers
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">3. Dynamic Data Injection</h3>
              <p className="text-gray-300 text-sm mb-4">
                Invoice data is safely injected into template placeholders with HTML escaping
              </p>
              
              <h3 className="font-semibold mb-2">4. PDF Export</h3>
              <p className="text-gray-300 text-sm">
                Clean HTML is converted to professional PDFs using WeasyPrint
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvoicePreviewDemo;