import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useInvoiceStore } from '../../../stores/invoiceStore';

import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';

const WorkflowTracker: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const { setWorkflowId, setUiInvoiceComponent } = useInvoiceStore();
  const [messages, setMessages] = useState<any[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [humanInputRequired, setHumanInputRequired] = useState<any | null>(null);
  const [humanInput, setHumanInput] = useState<any>({});

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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setHumanInput((prevInput: any) => ({ ...prevInput, [name]: value }));
  };

  const handleHumanInputSubmit = () => {
    if (socket) {
      const message = {
        type: 'human_input_submission',
        data: {
          field_values: humanInput,
          user_notes: 'User submitted input'
        }
      };
      socket.send(JSON.stringify(message));
      setHumanInputRequired(null);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-slate-900">Workflow Tracker</h1>
      <p className="text-slate-600 mt-2">Tracking workflow: {workflowId}</p>

      {humanInputRequired && (
        <Card>
          <CardHeader>
            <CardTitle>Human Input Required</CardTitle>
            <CardDescription>{humanInputRequired.message}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {humanInputRequired.fields.map((field: any) => (
              <div key={field.name}>
                <label className="block text-sm font-medium text-gray-700">{field.label}</label>
                <Input
                  name={field.name}
                  type={field.type}
                  value={humanInput[field.name] || ''}
                  onChange={handleInputChange}
                />
              </div>
            ))}
          </CardContent>
          <CardFooter>
            <Button onClick={handleHumanInputSubmit}>Submit</Button>
          </CardFooter>
        </Card>
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
