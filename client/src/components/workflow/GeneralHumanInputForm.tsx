import React, { useState } from 'react';
import { MessageSquare, Send, X, User, Clock, Info } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Textarea } from '../ui/Textarea';
import { Badge } from '../ui/Badge';

interface GeneralHumanInputProps {
  taskId: string;
  prompt: string;
  timestamp?: string;
  onSubmit: (taskId: string, userInput: string) => Promise<void>;
  onCancel?: () => void;
  isSubmitting?: boolean;
}

const GeneralHumanInputForm: React.FC<GeneralHumanInputProps> = ({
  taskId,
  prompt,
  timestamp,
  onSubmit,
  onCancel,
  isSubmitting = false
}) => {
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Allow empty input for testing - workflow can handle it
    // if (!userInput.trim()) {
    //   setError('Please provide some input before submitting');
    //   return;
    // }
    
    setIsLoading(true);
    setError(null);
    
    try {
      await onSubmit(taskId, userInput.trim() || 'Continue processing'); // Provide default if empty
      setUserInput(''); // Clear input after successful submission
    } catch (error) {
      console.error('Failed to submit human input:', error);
      setError(error instanceof Error ? error.message : 'Failed to submit input');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setUserInput('');
    setError(null);
    if (onCancel) {
      onCancel();
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  const isActuallySubmitting = isSubmitting || isLoading;

  return (
    <Card className="p-6 border-l-4 border-l-blue-400 bg-blue-50 shadow-md">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center">
            <MessageSquare className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Workflow Waiting for Input
            </h3>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant="primary" className="bg-blue-100 text-blue-800">
              <Clock className="h-3 w-3 mr-1" />
              Paused
            </Badge>
            
            {timestamp && (
              <span className="text-xs text-gray-500">
                {formatTimestamp(timestamp)}
              </span>
            )}
          </div>
        </div>
        
        <div className="mb-4 p-3 bg-white border border-blue-200 rounded-md">
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-gray-900 mb-1">
                Workflow Request:
              </p>
              <p className="text-sm text-gray-700">
                {prompt || 'Please provide input to continue the workflow'}
              </p>
            </div>
          </div>
        </div>

        {taskId && (
          <div className="mb-3">
            <p className="text-xs text-gray-500">
              <strong>Task ID:</strong> 
              <code className="ml-1 bg-gray-100 px-1 py-0.5 rounded text-xs">
                {taskId.substring(0, 8)}...
              </code>
            </p>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="flex items-center text-sm font-medium text-gray-700">
            <User className="h-4 w-4 mr-2" />
            Your Response
          </label>
          <Textarea
            value={userInput}
            onChange={(e) => {
              setUserInput(e.target.value);
              if (error) setError(null); // Clear error when user starts typing
            }}
            placeholder="Enter your response or provide the requested information..."
            rows={4}
            className="w-full resize-none"
            disabled={isActuallySubmitting}
          />
          
          <div className="flex justify-between text-xs text-gray-500">
            <span>
              {userInput.length > 0 ? `${userInput.length} characters` : 'No input provided'}
            </span>
            <span>
              Tip: Be specific and clear in your response
            </span>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700 flex items-center">
              <X className="h-4 w-4 mr-2 flex-shrink-0" />
              {error}
            </p>
          </div>
        )}

        <div className="flex space-x-3 pt-2">
          <Button
            type="submit"
            disabled={isActuallySubmitting}
            className="flex-1"
          >
            {isActuallySubmitting ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Submitting...
              </div>
            ) : (
              <div className="flex items-center">
                <Send className="mr-2 h-4 w-4" />
                Submit Response
              </div>
            )}
          </Button>
          
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isActuallySubmitting}
            >
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          )}
        </div>
      </form>

      <div className="mt-4 pt-4 border-t border-blue-200">
        <div className="flex items-start space-x-2 text-xs text-gray-600">
          <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium">What happens next:</p>
            <p>Once you submit your response, the workflow will automatically resume processing with your input.</p>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default GeneralHumanInputForm;