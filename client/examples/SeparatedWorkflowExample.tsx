import React, { useState } from 'react';
import { useContractStore } from '../stores/contractStore';

/**
 * Example component demonstrating the separated workflow approach:
 * 1. Sync contracts from Google Drive (no processing)
 * 2. User selects contracts to process
 * 3. Start agentic workflow for selected contracts
 */
export const SeparatedWorkflowExample: React.FC = () => {
  const {
    mcpContracts,
    mcpRentalContracts,
    isSyncingMCP,
    isSyncingRentals,
    mcpError,
    rentalError,
    syncMCPContracts,
    syncMCPRentalContracts,
    startInvoiceWorkflow
  } = useContractStore();

  const [selectedContracts, setSelectedContracts] = useState<string[]>([]);
  const [userId] = useState('user123'); // In real app, get from auth context

  // Phase 1: Sync contracts from Google Drive (no processing)
  const handleSyncAllContracts = async () => {
    try {
      await syncMCPContracts(); // No userId needed for sync-only
      console.log('✅ Contracts synced successfully');
    } catch (error) {
      console.error('❌ Sync failed:', error);
    }
  };

  const handleSyncRentalContracts = async () => {
    try {
      await syncMCPRentalContracts(); // No userId needed for sync-only
      console.log('✅ Rental contracts synced successfully');
    } catch (error) {
      console.error('❌ Rental sync failed:', error);
    }
  };

  // Phase 2: Start agentic workflow for selected contracts
  const handleProcessSelectedContracts = async () => {
    for (const contractName of selectedContracts) {
      try {
        // In a real app, you would download the file from Google Drive first
        // or pass the contract metadata to a workflow that can handle GDrive files
        console.log(`🔄 Starting workflow for: ${contractName}`);
        
        // This would require the actual file - in practice you might:
        // 1. Download from Google Drive using MCP
        // 2. Pass to agentic workflow
        // 3. Or create a new endpoint that accepts GDrive file IDs
        
        // await startInvoiceWorkflow(file, userId, contractName);
      } catch (error) {
        console.error(`❌ Failed to process ${contractName}:`, error);
      }
    }
  };

  const toggleContractSelection = (contractId: string) => {
    setSelectedContracts(prev => 
      prev.includes(contractId)
        ? prev.filter(id => id !== contractId)
        : [...prev, contractId]
    );
  };

  return (
    <div className="separated-workflow-example">
      <h2>📄 Contract Sync & Processing Workflow</h2>
      
      {/* Phase 1: Sync Controls */}
      <div className="sync-section">
        <h3>Phase 1: Sync Contracts from Google Drive</h3>
        <div className="sync-buttons">
          <button 
            onClick={handleSyncAllContracts} 
            disabled={isSyncingMCP}
            className="sync-btn"
          >
            {isSyncingMCP ? '⏳ Syncing...' : '📄 Sync All Contracts'}
          </button>
          
          <button 
            onClick={handleSyncRentalContracts} 
            disabled={isSyncingRentals}
            className="sync-btn"
          >
            {isSyncingRentals ? '⏳ Syncing...' : '🏠 Sync Rental Contracts'}
          </button>
        </div>

        {mcpError && (
          <div className="error">❌ Sync Error: {mcpError}</div>
        )}
        {rentalError && (
          <div className="error">❌ Rental Sync Error: {rentalError}</div>
        )}
      </div>

      {/* Phase 2: Contract Selection */}
      <div className="contracts-section">
        <h3>Available Contracts (Synced)</h3>
        
        {/* General Contracts */}
        {mcpContracts.length > 0 && (
          <div className="contract-group">
            <h4>📄 General Contracts ({mcpContracts.length})</h4>
            {mcpContracts.map(contract => (
              <div key={contract.file_id} className="contract-item">
                <label>
                  <input
                    type="checkbox"
                    checked={selectedContracts.includes(contract.file_id)}
                    onChange={() => toggleContractSelection(contract.file_id)}
                  />
                  <span className="contract-name">{contract.name}</span>
                  <span className="contract-type">({contract.mime_type})</span>
                </label>
              </div>
            ))}
          </div>
        )}

        {/* Rental Contracts */}
        {mcpRentalContracts.length > 0 && (
          <div className="contract-group">
            <h4>🏠 Rental Contracts ({mcpRentalContracts.length})</h4>
            {mcpRentalContracts.map(contract => (
              <div key={contract.file_id} className="contract-item">
                <label>
                  <input
                    type="checkbox"
                    checked={selectedContracts.includes(contract.file_id)}
                    onChange={() => toggleContractSelection(contract.file_id)}
                  />
                  <span className="contract-name">{contract.name}</span>
                  <span className="contract-type">({contract.mime_type}) 🏠</span>
                </label>
              </div>
            ))}
          </div>
        )}

        {mcpContracts.length === 0 && mcpRentalContracts.length === 0 && (
          <div className="empty-state">
            📭 No contracts synced yet. Click the sync buttons above to retrieve contracts from Google Drive.
          </div>
        )}
      </div>

      {/* Phase 3: Processing Controls */}
      <div className="processing-section">
        <h3>Phase 2: Process Selected Contracts</h3>
        <button
          onClick={handleProcessSelectedContracts}
          disabled={selectedContracts.length === 0}
          className="process-btn"
        >
          🚀 Start Agentic Workflow ({selectedContracts.length} selected)
        </button>

        <div className="workflow-info">
          <p>💡 <strong>Separated Workflow Benefits:</strong></p>
          <ul>
            <li>✅ Browse contracts before processing</li>
            <li>✅ Choose specific contracts for invoice generation</li>
            <li>✅ No unnecessary processing overhead during sync</li>
            <li>✅ Better control over processing costs</li>
          </ul>
        </div>
      </div>

      <style jsx>{`
        .separated-workflow-example {
          padding: 20px;
          max-width: 800px;
        }
        
        .sync-section, .contracts-section, .processing-section {
          margin-bottom: 30px;
          padding: 20px;
          border: 1px solid #e1e5e9;
          border-radius: 8px;
        }
        
        .sync-buttons {
          display: flex;
          gap: 10px;
          margin-bottom: 15px;
        }
        
        .sync-btn, .process-btn {
          padding: 10px 20px;
          border: none;
          border-radius: 6px;
          background: #007bff;
          color: white;
          cursor: pointer;
          font-size: 14px;
        }
        
        .sync-btn:disabled, .process-btn:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }
        
        .process-btn {
          background: #28a745;
          font-size: 16px;
          padding: 15px 25px;
        }
        
        .error {
          color: #dc3545;
          background: #f8d7da;
          padding: 10px;
          border-radius: 4px;
          margin: 10px 0;
        }
        
        .contract-group {
          margin-bottom: 20px;
        }
        
        .contract-item {
          margin: 5px 0;
          padding: 8px;
          background: #f8f9fa;
          border-radius: 4px;
        }
        
        .contract-item label {
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
        }
        
        .contract-name {
          font-weight: 500;
          flex-grow: 1;
        }
        
        .contract-type {
          color: #6c757d;
          font-size: 12px;
        }
        
        .empty-state {
          text-align: center;
          color: #6c757d;
          padding: 40px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        
        .workflow-info {
          margin-top: 20px;
          padding: 15px;
          background: #e7f3ff;
          border-radius: 6px;
        }
        
        .workflow-info ul {
          margin: 10px 0;
          padding-left: 20px;
        }
        
        .workflow-info li {
          margin: 5px 0;
        }
      `}</style>
    </div>
  );
};