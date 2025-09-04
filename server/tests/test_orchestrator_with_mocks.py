import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import json
from functools import wraps

def async_test(func):
    """Decorator to run async test methods"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        return asyncio.run(func(self, *args, **kwargs))
    return wrapper

from agents.orchestrator_agent import OrchestratorAgent
from workflows.invoice_workflow import run_invoice_workflow, initialize_workflow_state
from services.orchestrator_service import OrchestratorService
from schemas.workflow_schemas import WorkflowRequest, ProcessingStatus
from tests.mock_llm import MockLLMFactory, MockVertexAIModel, create_mock_model_function
from utils.langsmith_config import get_langsmith_config

class TestOrchestratorWithMocks(unittest.TestCase):
    """Comprehensive unittest suite with mocks for orchestrator testing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.orchestrator = OrchestratorAgent()
        self.mock_llm, self.mock_get_model = create_mock_model_function()
        self.langsmith_config = get_langsmith_config()
        
        # Test data
        self.test_request = WorkflowRequest(
            user_id="test_user_123",
            contract_file="test_contract.pdf", 
            contract_name="Test Rental Agreement",
            max_attempts=3
        )
        
    @patch('models.llm.base.get_model')
    def test_orchestrator_decision_making(self, mock_get_model):
        """Test orchestrator decision-making logic with mocked LLM"""
        mock_get_model.return_value = self.mock_llm
        
        # Test Case 1: Initial state should route to contract processing
        initial_state = initialize_workflow_state(
            "test_user", "test_contract.pdf", "Test Contract"
        )
        
        result_state = self.orchestrator.process(initial_state)
        decision = result_state.get("orchestrator_decision", {})
        
        self.assertEqual(decision["next_action"], "contract_processing")
        self.assertGreater(decision["confidence"], 0.8)
        self.assertIn("starting workflow", decision["reason"].lower())
        
    @patch('models.llm.base.get_model')
    def test_orchestrator_error_handling(self, mock_get_model):
        """Test orchestrator handling of error conditions"""
        # Create unreliable mock that fails sometimes
        unreliable_mock = MockLLMFactory.create_unreliable_llm(failure_rate=1.0)
        mock_get_model.return_value = unreliable_mock
        
        state = initialize_workflow_state("test_user", "test_contract.pdf", "Test Contract")
        
        # Should handle LLM failures gracefully
        result_state = self.orchestrator.process(state)
        
        # Should still have orchestrator decision even if LLM fails
        self.assertIn("orchestrator_decision", result_state)
        self.assertEqual(result_state["current_agent"], "orchestrator")
        
    @patch('models.llm.base.get_model')
    def test_orchestrator_max_attempts_logic(self, mock_get_model):
        """Test orchestrator behavior when max attempts reached"""
        mock_get_model.return_value = self.mock_llm
        
        state = initialize_workflow_state("test_user", "test_contract.pdf", "Test Contract")
        state["attempt_count"] = 3
        state["max_attempts"] = 3
        state["errors"] = [{"error": "test error"}] * 3
        
        result_state = self.orchestrator.process(state)
        decision = result_state.get("orchestrator_decision", {})
        
        self.assertEqual(decision["next_action"], "complete_with_errors")
        self.assertLess(decision["confidence"], 0.2)
        
    @patch('models.llm.base.get_model')
    def test_orchestrator_quality_based_routing(self, mock_get_model):
        """Test orchestrator routing based on quality scores"""
        mock_get_model.return_value = self.mock_llm
        
        # High quality should route to storage
        state = initialize_workflow_state("test_user", "test_contract.pdf", "Test Contract")
        state["quality_assurance_result"] = {
            "quality_score": 0.95,
            "status": "passed"
        }
        state["invoice_data"] = {"confidence": 0.9}
        
        result_state = self.orchestrator.process(state)
        decision = result_state.get("orchestrator_decision", {})
        
        self.assertEqual(decision["next_action"], "storage_scheduling")
        self.assertGreater(decision["confidence"], 0.8)
        
    @patch('services.contract_rag_service.get_contract_rag_service')
    @patch('models.llm.base.get_model')
    def test_workflow_with_mocked_services(self, mock_get_model, mock_rag_service):
        """Test complete workflow execution with mocked external services"""
        # Setup mocks
        mock_get_model.return_value = self.mock_llm
        
        mock_rag_service_instance = MagicMock()
        mock_rag_service.return_value = mock_rag_service_instance
        
        # Mock RAG service methods
        mock_rag_service_instance._retrieve_contract_context.return_value = "Sample contract content"
        mock_rag_service_instance.generate_invoice_data.return_value = MagicMock(
            confidence_score=0.85,
            model_dump=MagicMock(return_value={"mock": "invoice_data"})
        )
        
        # Create workflow and override the RAG service
        workflow = InvoiceWorkflow()
        workflow.contract_rag_service = mock_rag_service_instance
        
        # Test individual workflow nodes
        state = initialize_workflow_state("test_user", "test_contract.pdf", "Test Contract")
        
        # Test contract processing node
        processed_state = workflow._contract_processing_node(state)
        self.assertIn("contract_data", processed_state)
        self.assertEqual(processed_state["processing_status"], ProcessingStatus.SUCCESS.value)
        
        # Test validation node
        validated_state = workflow._validation_node(processed_state)
        self.assertIn("validation_results", validated_state)
        
    @async_test
    @patch('db.db.get_pinecone_client')
    @patch('models.llm.base.get_model')
    async def test_orchestrator_service_with_mocks(self, mock_get_model, mock_pinecone):
        """Test orchestrator service with all external dependencies mocked"""
        # Setup mocks
        mock_get_model.return_value = self.mock_llm
        
        mock_pinecone_instance = MagicMock()
        mock_pinecone.return_value = mock_pinecone_instance
        mock_pinecone_instance.query.return_value = MagicMock(
            matches=[
                MagicMock(metadata={"text": "Sample contract text"})
            ]
        )
        
        # Create service
        service = OrchestratorService()
        
        # Test workflow execution
        from unittest.mock import Mock
        mock_background_tasks = Mock()
        response = await service.start_invoice_workflow(self.test_request, mock_background_tasks)
        
        self.assertIsNotNone(response.workflow_id)
        self.assertIn(response.status, [ProcessingStatus.SUCCESS, ProcessingStatus.COMPLETED, ProcessingStatus.FAILED])
        self.assertGreaterEqual(response.processing_time_seconds, 0)
        
    def test_mock_llm_call_tracking(self):
        """Test that mock LLM properly tracks calls for debugging"""
        mock_llm = MockLLMFactory.create_reliable_llm()
        
        # Make some test calls
        response1 = mock_llm.invoke("Test input 1")
        response2 = mock_llm.invoke("Test input 2") 
        
        # Check call tracking
        self.assertEqual(mock_llm.get_call_count(), 2)
        
        call_history = mock_llm.get_call_history()
        self.assertEqual(len(call_history), 2)
        self.assertEqual(call_history[0]["input"], "Test input 1")
        self.assertEqual(call_history[1]["input"], "Test input 2")
        
        # Test reset
        mock_llm.reset_calls()
        self.assertEqual(mock_llm.get_call_count(), 0)
        
    @patch('utils.langsmith_config.get_langsmith_config')
    def test_langsmith_integration(self, mock_langsmith):
        """Test that LangSmith integration works with mocks"""
        mock_langsmith_instance = MagicMock()
        mock_langsmith.return_value = mock_langsmith_instance
        mock_langsmith_instance.is_enabled.return_value = True
        
        # Test that orchestrator produces valid output for LangSmith
        state = initialize_workflow_state("test_user", "test_contract.pdf", "Test Contract")
        result = self.orchestrator.process(state)
        
        # Verify orchestrator decision is created (this is what LangSmith would log)
        self.assertIn("orchestrator_decision", result)
        self.assertIn("next_action", result["orchestrator_decision"])
        self.assertIn("reason", result["orchestrator_decision"])
        self.assertEqual(result["current_agent"], "orchestrator")
        
    def test_orchestrator_consistency(self):
        """Test that orchestrator makes consistent decisions with same input"""
        state = initialize_workflow_state("test_user", "test_contract.pdf", "Test Contract")
        
        # Run orchestrator multiple times with same input
        results = []
        for _ in range(5):
            result_state = self.orchestrator.process(state.copy())
            decision = result_state.get("orchestrator_decision", {})
            results.append(decision["next_action"])
        
        # All decisions should be the same
        self.assertTrue(all(action == results[0] for action in results))
        
    def test_orchestrator_state_validation(self):
        """Test orchestrator handles invalid state gracefully"""
        # Test with missing required fields
        invalid_state = {
            "workflow_id": "test",
            # Missing many required fields
        }
        
        # Should not crash, should handle gracefully
        try:
            result_state = self.orchestrator.process(invalid_state)
            self.assertIsInstance(result_state, dict)
        except Exception as e:
            # Should fail gracefully, not with unexpected errors
            self.assertNotIn("KeyError", str(e))


class TestOrchestratorPerformance(unittest.TestCase):
    """Performance tests for orchestrator with mocks"""
    
    def setUp(self):
        self.orchestrator = OrchestratorAgent()
        self.mock_llm = MockLLMFactory.create_reliable_llm()
    
    @patch('models.llm.base.get_model')
    def test_orchestrator_performance(self, mock_get_model):
        """Test orchestrator performance with mocked LLM"""
        mock_get_model.return_value = self.mock_llm
        
        state = initialize_workflow_state("test_user", "test_contract.pdf", "Test Contract")
        
        # Time the orchestrator execution
        import time
        start_time = time.time()
        
        for _ in range(100):
            self.orchestrator.process(state.copy())
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        # Should be fast with mocked LLM (under 10ms per call)
        self.assertLess(avg_time, 0.01, f"Average orchestrator time: {avg_time:.4f}s")
        
    @patch('models.llm.base.get_model')
    def test_orchestrator_memory_usage(self, mock_get_model):
        """Test orchestrator doesn't have memory leaks"""
        mock_get_model.return_value = self.mock_llm
        
        import gc
        import sys
        
        # Get initial memory
        gc.collect()
        initial_refs = len(gc.get_objects())
        
        # Run orchestrator many times
        for i in range(1000):
            state = initialize_workflow_state(f"test_user_{i}", "test_contract.pdf", "Test Contract")
            self.orchestrator.process(state)
        
        # Check memory growth
        gc.collect()
        final_refs = len(gc.get_objects())
        
        # Should not have significant memory growth
        memory_growth = final_refs - initial_refs
        self.assertLess(memory_growth, 1000, f"Memory growth: {memory_growth} objects")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)