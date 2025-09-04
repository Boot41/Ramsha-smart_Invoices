import React, { useState } from 'react';
import ModernInvoiceTemplate from '../../components/invoices/ModernInvoiceTemplate';
import VintageInvoiceTemplate from '../../components/invoices/VintageInvoiceTemplate';
import MinimalistInvoiceTemplate from '../../components/invoices/MinimalistInvoiceTemplate';

const InvoiceTemplatesShowcase: React.FC = () => {
  const [selectedTemplate, setSelectedTemplate] = useState<'modern' | 'vintage' | 'minimalist'>('modern');

  // Sample data for templates
  const sampleInvoiceData = {
    contract_title: "Web Development Services",
    client: {
      name: "Acme Corporation",
      email: "contact@acme.com",
      address: "123 Business St, Suite 100, New York, NY 10001",
      phone: "+1 (555) 123-4567",
      tax_id: "TAX123456",
      role: "client"
    },
    service_provider: {
      name: "Digital Solutions LLC",
      email: "hello@digitalsolutions.com",
      address: "456 Tech Avenue, San Francisco, CA 94102",
      phone: "+1 (555) 987-6543",
      tax_id: "TAX789012",
      role: "service_provider"
    },
    payment_terms: {
      amount: 2500,
      currency: "USD",
      frequency: "monthly" as const,
      due_days: 30,
      late_fee: 50,
      discount_terms: "2% discount if paid within 10 days"
    },
    services: [
      {
        description: "Website Development & Design",
        quantity: 1,
        unit_price: 1500,
        total_amount: 1500,
        unit: "project"
      },
      {
        description: "SEO Optimization",
        quantity: 1,
        unit_price: 500,
        total_amount: 500,
        unit: "service"
      },
      {
        description: "Monthly Maintenance",
        quantity: 1,
        unit_price: 500,
        total_amount: 500,
        unit: "month"
      }
    ],
    special_terms: "All work completed according to specifications outlined in the contract dated March 1, 2024.",
    notes: "Thank you for choosing Digital Solutions LLC. We look forward to continuing our partnership with Acme Corporation."
  };

  const templates = [
    {
      id: 'modern',
      name: 'Modern',
      description: 'Clean, gradient-rich design perfect for tech companies and modern businesses',
      component: <ModernInvoiceTemplate invoiceData={sampleInvoiceData} amount={2500} />
    },
    {
      id: 'vintage',
      name: 'Vintage',
      description: 'Classic, elegant design with ornate details for established businesses',
      component: <VintageInvoiceTemplate invoiceData={sampleInvoiceData} amount={2500} />
    },
    {
      id: 'minimalist',
      name: 'Minimalist',
      description: 'Ultra-clean, typography-focused design for professional service providers',
      component: <MinimalistInvoiceTemplate invoiceData={sampleInvoiceData} amount={2500} />
    }
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Invoice Templates Showcase</h1>
              <p className="mt-2 text-gray-600">Professional invoice templates inspired by modern design trends</p>
            </div>
            <div className="flex space-x-4">
              {templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => setSelectedTemplate(template.id as any)}
                  className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                    selectedTemplate === template.id
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {template.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div
                key={template.id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                  selectedTemplate === template.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedTemplate(template.id as any)}
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{template.name} Template</h3>
                <p className="text-sm text-gray-600 mb-4">{template.description}</p>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    selectedTemplate === template.id ? 'bg-blue-500' : 'bg-gray-300'
                  }`}></div>
                  <span className="text-sm font-medium text-gray-700">
                    {selectedTemplate === template.id ? 'Selected' : 'Click to preview'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">
              {templates.find(t => t.id === selectedTemplate)?.name} Template Preview
            </h2>
            <div className="flex space-x-3">
              <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                Use This Template
              </button>
              <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
                Download PDF
              </button>
            </div>
          </div>
          
          <div className="transform scale-75 origin-top-left w-full overflow-hidden">
            <div className="w-[133%]"> {/* Compensate for scale */}
              {templates.find(t => t.id === selectedTemplate)?.component}
            </div>
          </div>
        </div>

        <div className="mt-8 bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Template Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🎨</span>
              </div>
              <h4 className="font-medium text-gray-900 mb-2">Professional Design</h4>
              <p className="text-sm text-gray-600">Beautiful, modern layouts that make a great impression</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">⚡</span>
              </div>
              <h4 className="font-medium text-gray-900 mb-2">Fully Customizable</h4>
              <p className="text-sm text-gray-600">Easily modify colors, fonts, and layout to match your brand</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">📱</span>
              </div>
              <h4 className="font-medium text-gray-900 mb-2">Print Ready</h4>
              <p className="text-sm text-gray-600">Optimized for both digital viewing and professional printing</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvoiceTemplatesShowcase;