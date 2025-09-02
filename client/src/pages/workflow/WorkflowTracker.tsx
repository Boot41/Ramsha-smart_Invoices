import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useInvoiceStore } from '../../../stores/invoiceStore';
import { workflowAPI } from '../../services/workflowService';

import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import HumanInputForm from '../../components/workflow/HumanInputForm';

const WorkflowTracker: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const { setWorkflowId, setUiInvoiceComponent } = useInvoiceStore();
  const [messages, setMessages] = useState<any[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [humanInputRequired, setHumanInputRequired] = useState<any | null>(null);

  useEffect(() => {
    if (workflowId) {
      setWorkflowId(workflowId);
      const ws = new WebSocket(`ws://localhost:8000/api/v1/orchestrator/ws/workflow/${workflowId}/realtime`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setSocket(ws);
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        setMessages((prevMessages) => [...prevMessages, message]);

        if (message.type === 'human_input_required') {
          setHumanInputRequired(message.data);
        } else if (message.type === 'agent_completed' && message.data.agent === 'ui_invoice_generator') {
          setUiInvoiceComponent(message.data.component_details);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setSocket(null);
      };

      return () => {
        ws.close();
      };
    }
  }, [workflowId, setWorkflowId, setUiInvoiceComponent]);

  const handleHumanInputSubmit = async (fieldValues: Record<string, any>, userNotes: string) => {
    try {
      // Try WebSocket first (real-time)
      if (socket && socket.readyState === WebSocket.OPEN) {
        const message = {
          type: 'human_input_submission',
          data: {
            field_values: fieldValues,
            user_notes: userNotes
          }
        };
        socket.send(JSON.stringify(message));
        console.log('✅ Human input submitted via WebSocket');
      } else {
        // Fallback to HTTP API if WebSocket is not available
        console.log('🔄 WebSocket not available, using HTTP API fallback...');
        await workflowAPI.submitHumanInput(workflowId!, fieldValues, userNotes);
        console.log('✅ Human input submitted via HTTP API');
      }
      
      setHumanInputRequired(null);
    } catch (error) {
      console.error('❌ Failed to submit human input:', error);
      // You could show a user-friendly error message here
      alert('Failed to submit input. Please try again.');
    }
  };

  const handleHumanInputCancel = () => {
    setHumanInputRequired(null);
    // Optionally send a cancellation message to the workflow
    if (socket) {
      const message = {
        type: 'human_input_cancelled',
        data: {
          message: 'User cancelled human input'
        }
      };
      socket.send(JSON.stringify(message));
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-slate-900">Workflow Tracker</h1>
      <p className="text-slate-600 mt-2">Tracking workflow: {workflowId}</p>

      {humanInputRequired && (
        <HumanInputForm
          request={{
            fields: humanInputRequired.fields || [],
            instructions: humanInputRequired.instructions || humanInputRequired.message || 'Please review and correct the extracted data.',
            context: humanInputRequired.context || {},
            validation_errors: humanInputRequired.validation_errors || [],
            confidence_scores: humanInputRequired.confidence_scores || {}
          }}
          onSubmit={handleHumanInputSubmit}
          onCancel={handleHumanInputCancel}
        />
      )}

      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Workflow Events</h2>
        <div className="space-y-4">
          {messages.map((msg, index) => (
            <div key={index} className="bg-gray-100 p-4 rounded-lg">
              <pre>{JSON.stringify(msg, null, 2)}</pre>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WorkflowTracker;
