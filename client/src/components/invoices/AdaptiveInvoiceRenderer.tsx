import React from 'react';
import { Header, ClientInfo, LineItemTable, Summary } from './invoice-parts';
import type { InvoiceComponent } from '../../services/api';

interface AdaptiveInvoiceRendererProps {
  uiDefinition?: {
    design_name: string;
    design_id: string;
    style_theme: string;
    components: InvoiceComponent[];
  };
}

// Component mapping for rendering different component types
const componentMap = {
  header: Header,
  client_info: ClientInfo,
  line_items: LineItemTable,
  summary: Summary,
};

export const AdaptiveInvoiceRenderer: React.FC<AdaptiveInvoiceRendererProps> = ({
  uiDefinition
}) => {
  if (!uiDefinition || !uiDefinition.components) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>No design definition available</p>
      </div>
    );
  }

  // Apply theme-based styles
  const getThemeStyles = (theme: string): React.CSSProperties => {
    switch (theme) {
      case 'minimalist':
        return {
          fontFamily: 'Arial, sans-serif',
          backgroundColor: '#ffffff',
          color: '#2c3e50',
          padding: '40px',
          lineHeight: '1.6'
        };
      case 'classic':
        return {
          fontFamily: 'Georgia, serif',
          backgroundColor: '#fefefe',
          color: '#333333',
          padding: '40px',
          lineHeight: '1.7',
          border: '1px solid #e0e0e0'
        };
      case 'creative':
        return {
          fontFamily: 'Helvetica, sans-serif',
          backgroundColor: '#f8f9fa',
          color: '#2d3748',
          padding: '40px',
          lineHeight: '1.6',
          borderLeft: '4px solid #3182ce'
        };
      default:
        return {
          fontFamily: 'Arial, sans-serif',
          backgroundColor: '#ffffff',
          color: '#333333',
          padding: '40px'
        };
    }
  };

  const containerStyle = getThemeStyles(uiDefinition.style_theme);

  return (
    <div className="adaptive-invoice" style={containerStyle}>
      <div className="space-y-6">
        {uiDefinition.components.map((component, index) => {
          const ComponentToRender = componentMap[component.type as keyof typeof componentMap];
          
          if (!ComponentToRender) {
            console.warn(`Unknown component type: ${component.type}`);
            return null;
          }

          // Merge component styling with props
          const componentStyle: React.CSSProperties = {
            ...component.styling,
            // Convert string values that should be numbers
            ...(component.styling?.padding && !isNaN(Number(component.styling.padding.replace('px', ''))) && {
              padding: component.styling.padding
            }),
            ...(component.styling?.margin && !isNaN(Number(component.styling.margin.replace('px', ''))) && {
              margin: component.styling.margin
            })
          };

          return (
            <ComponentToRender
              key={index}
              {...component.props}
              style={componentStyle}
              className={component.styling?.className || ''}
            />
          );
        })}
      </div>
    </div>
  );
};