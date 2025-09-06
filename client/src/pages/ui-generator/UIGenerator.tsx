import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';
import { Palette, Code, Eye, Download, Upload, Sparkles } from 'lucide-react';

interface UIGeneratorProps {}

const UIGenerator: React.FC<UIGeneratorProps> = () => {
  const [data, setData] = useState<Record<string, any>>({});
  const [newField, setNewField] = useState({ key: '', value: '' });
  const [templateStyle, setTemplateStyle] = useState('modern');
  const [previewHtml, setPreviewHtml] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Sample data options
  const sampleDataOptions = [
    { value: 'invoice', label: '📄 Invoice Data' },
    { value: 'contract', label: '📋 Contract Data' },
    { value: 'report', label: '📊 Report Data' },
    { value: 'custom', label: '🎨 Custom Data' }
  ];

  const styleOptions = [
    { value: 'modern', label: '🎨 Modern' },
    { value: 'classic', label: '🏛️ Classic' },
    { value: 'minimal', label: '✨ Minimal' },
    { value: 'professional', label: '👔 Professional' }
  ];

  useEffect(() => {
    // Generate live preview when data changes
    if (Object.keys(data).length > 0) {
      generateLivePreview();
    }
  }, [data, templateStyle]);

  const addDataField = () => {
    if (newField.key && newField.value) {
      setData(prev => ({
        ...prev,
        [newField.key]: newField.value
      }));
      setNewField({ key: '', value: '' });
    }
  };

  const removeDataField = (key: string) => {
    setData(prev => {
      const newData = { ...prev };
      delete newData[key];
      return newData;
    });
  };

  const loadSampleData = async (type: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/ui-generator/sample-data/${type}`);
      if (!response.ok) throw new Error('Failed to load sample data');
      
      const result = await response.json();
      setData(result.sample_data || {});
      setSuccess('Sample data loaded successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sample data');
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const generateLivePreview = async () => {
    if (Object.keys(data).length === 0) {
      setPreviewHtml('<div class="preview-placeholder">Add some data to see the preview</div>');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/ui-generator/live-preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data,
          style: templateStyle
        })
      });

      if (!response.ok) throw new Error('Failed to generate preview');
      
      const result = await response.json();
      setPreviewHtml(result.html || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate preview');
      setPreviewHtml('<div class="error-placeholder">Failed to generate preview</div>');
    } finally {
      setIsLoading(false);
    }
  };

  const generateFullUITemplate = async () => {
    if (Object.keys(data).length === 0) {
      setError('Please add some data first');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/ui-generator/generate-ui', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data,
          template_type: 'invoice',
          layout_preferences: templateStyle
        })
      });

      if (!response.ok) throw new Error('Failed to generate UI template');
      
      const result = await response.json();
      
      // Create downloadable HTML file
      const fullHtml = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Generated UI Template</title>
          <style>${result.css_content}</style>
        </head>
        <body>
          ${result.html_content}
        </body>
        </html>
      `;
      
      const blob = new Blob([fullHtml], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ui-template-${Date.now()}.html`;
      a.click();
      URL.revokeObjectURL(url);
      
      setSuccess('UI template generated and downloaded!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate UI template');
    } finally {
      setIsLoading(false);
    }
  };

  const importDataFromJson = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const jsonData = JSON.parse(e.target?.result as string);
        setData(jsonData);
        setSuccess('JSON data imported successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        setError('Invalid JSON file format');
        setTimeout(() => setError(null), 5000);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-purple-600" />
            UI Generator
          </h1>
          <p className="text-slate-600 mt-2">
            Create beautiful UI templates with your data in real-time
          </p>
        </div>
        
        <div className="flex gap-3">
          <input
            type="file"
            accept=".json"
            onChange={importDataFromJson}
            className="hidden"
            id="json-upload"
          />
          <Button 
            variant="outline" 
            onClick={() => document.getElementById('json-upload')?.click()}
            className="flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Import JSON
          </Button>
          
          <Button 
            onClick={generateFullUITemplate}
            disabled={isLoading || Object.keys(data).length === 0}
            className="flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Generate & Download
          </Button>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}
      
      {success && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-700">{success}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Input Section */}
        <div className="space-y-6">
          {/* Quick Start with Sample Data */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5" />
                Quick Start
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {sampleDataOptions.map((option) => (
                  <Button
                    key={option.value}
                    variant="outline"
                    size="sm"
                    onClick={() => loadSampleData(option.value)}
                    disabled={isLoading}
                    className="text-left justify-start"
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
              
              <div>
                <label className="text-sm font-medium text-slate-700 mb-2 block">
                  Template Style
                </label>
                <Select
                  options={styleOptions}
                  value={templateStyle}
                  onChange={setTemplateStyle}
                  placeholder="Choose style"
                />
              </div>
            </CardContent>
          </Card>

          {/* Custom Data Entry */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="w-5 h-5" />
                Custom Data Fields
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Field name (e.g., company_name)"
                  value={newField.key}
                  onChange={(e) => setNewField(prev => ({ ...prev, key: e.target.value }))}
                />
                <Input
                  placeholder="Field value (e.g., Acme Corp)"
                  value={newField.value}
                  onChange={(e) => setNewField(prev => ({ ...prev, value: e.target.value }))}
                />
                <Button onClick={addDataField} disabled={!newField.key || !newField.value}>
                  Add
                </Button>
              </div>

              {/* Current Data Fields */}
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {Object.entries(data).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-slate-900">{key}</div>
                      <div className="text-sm text-slate-600 truncate">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeDataField(key)}
                      className="ml-2"
                    >
                      Remove
                    </Button>
                  </div>
                ))}
                
                {Object.keys(data).length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    No data fields added yet. Use quick start or add custom fields.
                  </div>
                )}
              </div>
              
              {Object.keys(data).length > 0 && (
                <div className="flex items-center gap-2 pt-2 border-t">
                  <Badge variant="secondary">
                    {Object.keys(data).length} fields
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setData({})}
                    className="text-red-600 hover:text-red-700"
                  >
                    Clear All
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Live Preview Section */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5" />
                Live Preview
                {isLoading && (
                  <div className="ml-2 w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg bg-white min-h-96 overflow-hidden">
                {previewHtml ? (
                  <div 
                    className="p-4"
                    dangerouslySetInnerHTML={{ __html: previewHtml }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-96 text-slate-500">
                    <div className="text-center">
                      <Eye className="w-12 h-12 mx-auto mb-4 opacity-30" />
                      <p>Add data to see live preview</p>
                      <p className="text-sm mt-1">Your UI will appear here in real-time</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Template Info */}
          {Object.keys(data).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Template Info</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Data Fields:</span>
                    <Badge>{Object.keys(data).length}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Style:</span>
                    <Badge variant="secondary">{templateStyle}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Template Type:</span>
                    <Badge variant="secondary">Auto-detected</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default UIGenerator;