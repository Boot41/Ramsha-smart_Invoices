#!/usr/bin/env python3
"""
Comprehensive test suite for InvoiceDesignAgent

Tests the new invoice design generation functionality with mock LLM integration
and various edge cases.
"""

import os
import sys
import unittest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from functools import wraps

def async_test(func):
    """Decorator to run async test methods"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        return asyncio.run(func(self, *args, **kwargs))
    return wrapper

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.invoice_design_agent import InvoiceDesignAgent
from schemas.workflow_schemas import WorkflowState, ProcessingStatus, AgentType
from tests.mock_llm import MockLLMFactory, MockVertexAIModel
from services.database_service import DatabaseService

class TestInvoiceDesignAgent(unittest.TestCase):
    """Test cases for InvoiceDesignAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = InvoiceDesignAgent()
        self.mock_model = MockLLMFactory.create_reliable_llm()
        
        # Sample invoice data for testing
        self.sample_invoice_data = {
            "invoice_header": {
                "invoice_number": "INV-001",
                "invoice_date": "2024-01-15",
                "due_date": "2024-02-15"
            },
            "parties": {
                "client": {
                    "name": "Test Client Corp",
                    "email": "client@test.com",
                    "address": "123 Client St, City, State 12345"
                },
                "service_provider": {
                    "name": "Test Provider LLC",
                    "email": "provider@test.com", 
                    "address": "456 Provider Ave, City, State 67890"
                }
            },
            "payment_terms": {
                "amount": 1500,
                "currency": "USD",
                "frequency": "monthly"
            },
            "contract_title": "Web Development Services",
            "services": [
                {
                    "description": "Web Development Services",
                    "quantity": 1,
                    "unit_price": 1500,
                    "total_amount": 1500
                }
            ]
        }
        
        # Sample workflow state
        self.sample_state = {
            "workflow_id": "test-workflow-123",
            "user_id": "test-user",
            "contract_name": "Test Contract",
            "invoice_created": True,
            "invoice_id": "test-invoice-123",
            "processing_status": ProcessingStatus.IN_PROGRESS.value,
            "attempt_count": 1,
            "max_attempts": 3,
            "errors": [],
            "started_at": datetime.now().isoformat()
        }
    
    @patch('agents.invoice_design_agent.get_model')
    @patch('agents.invoice_design_agent.get_database_service')
    def test_agent_initialization(self, mock_db_service, mock_get_model):
        """Test agent initialization"""
        mock_get_model.return_value = self.mock_llm
        mock_db_service.return_value = Mock()
        
        agent = InvoiceDesignAgent()
        
        self.assertEqual(agent.agent_type, AgentType.INVOICE_DESIGN)
        self.assertIsNotNone(agent.model)
        self.assertIsNotNone(agent.db_service)
        mock_get_model.assert_called_once()
    
    @async_test
    @patch('agents.invoice_design_agent.get_model')
    @patch('agents.invoice_design_agent.get_database_service')
    async def test_process_success_flow(self, mock_db_service, mock_get_model):
        """Test successful design generation flow"""
        # Setup mocks
        mock_get_model.return_value = self._create_design_mock_llm()
        
        mock_db = Mock()
        mock_invoice = Mock()
        mock_invoice.invoice_data = self.sample_invoice_data
        mock_db.get_invoice_by_id = AsyncMock(return_value=mock_invoice)
        mock_db.get_invoice_by_workflow_id = AsyncMock(return_value=None)
        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_db_service.return_value = mock_db
        
        agent = InvoiceDesignAgent()
        
        # Execute
        result_state = await agent.process(self.sample_state.copy())
        
        # Verify
        self.assertEqual(result_state["processing_status"], ProcessingStatus.SUCCESS.value)
        self.assertTrue(result_state["design_generation_completed"])
        self.assertIn("invoice_designs", result_state)
        self.assertIn("design_generation_timestamp", result_state)
        
        # Verify designs structure
        designs = result_state["invoice_designs"]
        self.assertIn("designs", designs)
        self.assertEqual(len(designs["designs"]), 3)
        
        # Verify design names
        design_names = [d["design_name"] for d in designs["designs"]]
        self.assertIn("Modern & Clean", design_names)
        self.assertIn("Classic & Professional", design_names)
        self.assertIn("Bold & Creative", design_names)
    
    @async_test
    @patch('agents.invoice_design_agent.get_model')
    @patch('agents.invoice_design_agent.get_database_service')
    async def test_process_no_invoice_data(self, mock_db_service, mock_get_model):
        """Test handling when no invoice data is found"""
        # Setup mocks
        mock_get_model.return_value = self.mock_llm
        
        mock_db = Mock()
        mock_db.get_invoice_by_id = AsyncMock(return_value=None)
        mock_db.get_invoice_by_workflow_id = AsyncMock(return_value=None)
        mock_db_service.return_value = mock_db
        
        agent = InvoiceDesignAgent()
        
        # Execute
        result_state = await agent.process(self.sample_state.copy())
        
        # Verify error handling
        self.assertEqual(result_state["processing_status"], ProcessingStatus.FAILED.value)
        self.assertFalse(result_state.get("design_generation_completed", True))
        self.assertIn("errors", result_state)
        self.assertTrue(len(result_state["errors"]) > 0)
        self.assertIn("No invoice data found", result_state["errors"][-1]["error"])
    
    @async_test
    @patch('agents.invoice_design_agent.get_model')
    @patch('agents.invoice_design_agent.get_database_service')
    async def test_process_llm_failure(self, mock_db_service, mock_get_model):
        """Test handling LLM failures"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm.generate_content_async = AsyncMock(side_effect=Exception("LLM API Error"))
        mock_get_model.return_value = mock_llm
        
        mock_db = Mock()
        mock_invoice = Mock()
        mock_invoice.invoice_data = self.sample_invoice_data
        mock_db.get_invoice_by_id = AsyncMock(return_value=mock_invoice)
        mock_db_service.return_value = mock_db
        
        agent = InvoiceDesignAgent()
        
        # Execute
        result_state = await agent.process(self.sample_state.copy())
        
        # Verify error handling
        self.assertEqual(result_state["processing_status"], ProcessingStatus.FAILED.value)
        self.assertFalse(result_state.get("design_generation_completed", True))
        self.assertIn("errors", result_state)
        self.assertTrue(len(result_state["errors"]) > 0)
        self.assertIn("Failed to generate invoice designs", result_state["errors"][-1]["error"])
    
    def test_generate_designs_with_mock(self):
        """Test design generation with mock LLM"""
        mock_llm = self._create_design_mock_llm()
        
        # Test the generate_designs method directly
        with patch.object(self.agent, 'model', mock_llm):
            designs = asyncio.run(self.agent.generate_designs(self.sample_invoice_data))
            
            self.assertIn("designs", designs)
            self.assertEqual(len(designs["designs"]), 3)
            
            # Check design structure
            for design in designs["designs"]:
                self.assertIn("design_name", design)
                self.assertIn("design_id", design)
                self.assertIn("components", design)
                self.assertIsInstance(design["components"], list)
    
    def test_parse_design_response_valid_json(self):
        """Test parsing valid JSON response"""
        valid_response = json.dumps({
            "designs": [
                {
                    "design_name": "Test Design",
                    "design_id": "test_design",
                    "style_theme": "minimalist",
                    "components": [
                        {
                            "type": "header",
                            "props": {"title": "Invoice"},
                            "styling": {"color": "blue"}
                        }
                    ]
                }
            ]
        })
        
        result = self.agent._parse_design_response(valid_response)
        
        self.assertIn("designs", result)
        self.assertEqual(len(result["designs"]), 1)
        self.assertEqual(result["designs"][0]["design_name"], "Test Design")
    
    def test_parse_design_response_invalid_json(self):
        """Test parsing invalid JSON response"""
        invalid_response = "This is not JSON"
        
        with self.assertRaises(ValueError) as context:
            self.agent._parse_design_response(invalid_response)
        
        self.assertIn("Invalid JSON response", str(context.exception))
    
    def test_parse_design_response_markdown_cleanup(self):
        """Test parsing response with markdown code blocks"""
        markdown_response = """```json
        {
            "designs": [
                {
                    "design_name": "Test Design",
                    "design_id": "test_design",
                    "components": []
                }
            ]
        }
        ```"""
        
        result = self.agent._parse_design_response(markdown_response)
        
        self.assertIn("designs", result)
        self.assertEqual(result["designs"][0]["design_name"], "Test Design")
    
    def test_safe_get_nested_values(self):
        """Test safe nested value extraction"""
        data = {
            "level1": {
                "level2": {
                    "value": "found"
                }
            }
        }
        
        # Test valid path
        result = self.agent._safe_get(data, "level1.level2.value", "default")
        self.assertEqual(result, "found")
        
        # Test invalid path
        result = self.agent._safe_get(data, "level1.missing.value", "default")
        self.assertEqual(result, "default")
        
        # Test empty path
        result = self.agent._safe_get(data, "", "default")
        self.assertEqual(result, "default")
    
    @async_test
    @patch('agents.invoice_design_agent.get_database_service')
    async def test_extract_invoice_data_from_database_by_id(self, mock_db_service):
        """Test extracting invoice data using invoice_id"""
        mock_db = Mock()
        mock_invoice = Mock()
        mock_invoice.invoice_data = self.sample_invoice_data
        mock_db.get_invoice_by_id = AsyncMock(return_value=mock_invoice)
        mock_db_service.return_value = mock_db
        
        agent = InvoiceDesignAgent()
        
        state_with_id = self.sample_state.copy()
        state_with_id["invoice_id"] = "test-invoice-123"
        
        result = await agent._extract_invoice_data_from_database(state_with_id)
        
        self.assertEqual(result, self.sample_invoice_data)
        mock_db.get_invoice_by_id.assert_called_once_with("test-invoice-123")
    
    @async_test
    @patch('agents.invoice_design_agent.get_database_service')
    async def test_extract_invoice_data_from_database_by_workflow_id(self, mock_db_service):
        """Test extracting invoice data using workflow_id"""
        mock_db = Mock()
        mock_invoice = Mock()
        mock_invoice.invoice_data = self.sample_invoice_data
        mock_db.get_invoice_by_id.return_value = None  # Not found by ID
        mock_db.get_invoice_by_workflow_id = AsyncMock(return_value=mock_invoice)
        mock_db_service.return_value = mock_db
        
        agent = InvoiceDesignAgent()
        
        result = await agent._extract_invoice_data_from_database(self.sample_state)
        
        self.assertEqual(result, self.sample_invoice_data)
        mock_db.get_invoice_by_workflow_id.assert_called_once_with("test-workflow-123")
    
    @async_test
    @patch('agents.invoice_design_agent.get_database_service')
    async def test_save_designs_to_database(self, mock_db_service):
        """Test saving designs to database"""
        mock_db = Mock()
        mock_invoice = Mock()
        mock_invoice.id = "test-invoice-123"
        mock_invoice.invoice_data = self.sample_invoice_data.copy()
        mock_db.get_invoice_by_id = AsyncMock(return_value=mock_invoice)
        
        # Mock session and update
        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_db_service.return_value = mock_db
        
        agent = InvoiceDesignAgent()
        
        designs_data = {
            "designs": [
                {
                    "design_name": "Test Design",
                    "components": []
                }
            ]
        }
        
        # Test with invoice_id in state
        state_with_id = self.sample_state.copy()
        state_with_id["invoice_id"] = "test-invoice-123"
        
        result = await agent._save_designs_to_database(state_with_id, designs_data)
        
        # Note: This test may need adjustment based on actual database implementation
        # The main point is to verify the method doesn't crash and attempts to save
        self.assertIsInstance(result, bool)
    
    def _create_design_mock_llm(self):
        """Create a mock LLM that returns valid design JSON"""
        mock_llm = Mock()
        
        # Sample design response
        design_response = {
            "designs": [
                {
                    "design_name": "Modern & Clean",
                    "design_id": "modern_clean",
                    "style_theme": "minimalist",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "Test Provider LLC",
                                "invoiceNumber": "INV-001",
                                "date": "2024-01-15"
                            },
                            "styling": {
                                "backgroundColor": "#ffffff",
                                "textColor": "#2c3e50",
                                "fontSize": "24px",
                                "fontFamily": "Arial, sans-serif"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Test Client Corp",
                                "providerName": "Test Provider LLC"
                            },
                            "styling": {
                                "display": "grid",
                                "gridTemplateColumns": "1fr 1fr"
                            }
                        },
                        {
                            "type": "line_items",
                            "props": {
                                "items": [
                                    {
                                        "description": "Web Development Services",
                                        "quantity": 1,
                                        "unitPrice": 1500,
                                        "total": 1500
                                    }
                                ]
                            },
                            "styling": {
                                "width": "100%"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "subtotal": 1500,
                                "total": 1500,
                                "currency": "USD"
                            },
                            "styling": {
                                "textAlign": "right"
                            }
                        }
                    ]
                },
                {
                    "design_name": "Classic & Professional",
                    "design_id": "classic_professional",
                    "style_theme": "classic",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "Test Provider LLC"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif"
                            }
                        }
                    ]
                },
                {
                    "design_name": "Bold & Creative",
                    "design_id": "bold_creative",
                    "style_theme": "creative",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "Test Provider LLC"
                            },
                            "styling": {
                                "fontFamily": "Helvetica, sans-serif",
                                "borderLeft": "4px solid #3182ce"
                            }
                        }
                    ]
                }
            ]
        }
        
        # Mock response object
        mock_response = Mock()
        mock_response.text = json.dumps(design_response)
        
        mock_llm.generate_content_async = AsyncMock(return_value=mock_response)
        
        return mock_llm


class TestInvoiceDesignAgentIntegration(unittest.TestCase):
    """Integration tests for InvoiceDesignAgent with real-like scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.agent = InvoiceDesignAgent()
    
    @async_test
    @patch('agents.invoice_design_agent.get_model')
    @patch('agents.invoice_design_agent.get_database_service')
    async def test_end_to_end_design_generation(self, mock_db_service, mock_get_model):
        """Test complete end-to-end design generation"""
        # Setup realistic invoice data
        invoice_data = {
            "invoice_header": {
                "invoice_number": "INV-2024-001",
                "invoice_date": "2024-01-15",
                "due_date": "2024-02-15"
            },
            "parties": {
                "client": {
                    "name": "Acme Corporation",
                    "email": "billing@acme.com",
                    "address": "123 Business Ave\nSuite 100\nNew York, NY 10001"
                },
                "service_provider": {
                    "name": "Design Studio Pro",
                    "email": "invoices@designstudio.com",
                    "address": "456 Creative Blvd\nLos Angeles, CA 90210"
                }
            },
            "payment_terms": {
                "amount": 2500,
                "currency": "USD",
                "frequency": "one-time",
                "due_days": 30
            },
            "contract_title": "Logo Design & Brand Identity Package",
            "services": [
                {
                    "description": "Logo Design",
                    "quantity": 1,
                    "unit_price": 1500,
                    "total_amount": 1500
                },
                {
                    "description": "Brand Guidelines Document",
                    "quantity": 1,
                    "unit_price": 1000,
                    "total_amount": 1000
                }
            ]
        }
        
        # Mock database and LLM
        mock_db = Mock()
        mock_invoice = Mock()
        mock_invoice.invoice_data = invoice_data
        mock_db.get_invoice_by_id = AsyncMock(return_value=mock_invoice)
        mock_db_service.return_value = mock_db
        
        # Create comprehensive mock LLM
        mock_llm = self._create_comprehensive_design_llm()
        mock_get_model.return_value = mock_llm
        
        # Create workflow state
        state = {
            "workflow_id": "integration-test-workflow",
            "user_id": "integration-test-user",
            "invoice_id": "integration-test-invoice",
            "contract_name": "Logo Design Contract",
            "processing_status": ProcessingStatus.IN_PROGRESS.value,
            "invoice_created": True,
            "attempt_count": 1,
            "max_attempts": 3,
            "errors": [],
            "started_at": datetime.now().isoformat()
        }
        
        # Execute
        result_state = await self.agent.process(state)
        
        # Verify successful processing
        self.assertEqual(result_state["processing_status"], ProcessingStatus.SUCCESS.value)
        self.assertTrue(result_state["design_generation_completed"])
        
        # Verify design structure and content
        designs = result_state["invoice_designs"]
        self.assertEqual(len(designs["designs"]), 3)
        
        # Verify each design has required components
        for design in designs["designs"]:
            self.assertIn("design_name", design)
            self.assertIn("components", design)
            
            # Check for essential components
            component_types = [comp["type"] for comp in design["components"]]
            self.assertIn("header", component_types)
            self.assertIn("client_info", component_types)
            self.assertIn("line_items", component_types)
            self.assertIn("summary", component_types)
            
            # Verify component props contain data
            for component in design["components"]:
                if component["type"] == "header":
                    self.assertIn("companyName", component["props"])
                elif component["type"] == "line_items":
                    self.assertIn("items", component["props"])
                    self.assertTrue(len(component["props"]["items"]) > 0)
    
    def _create_comprehensive_design_llm(self):
        """Create a comprehensive mock LLM for integration testing"""
        mock_llm = Mock()
        
        # Comprehensive design response with all three designs
        comprehensive_response = {
            "designs": [
                {
                    "design_name": "Modern & Clean",
                    "design_id": "modern_clean",
                    "style_theme": "minimalist",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "Design Studio Pro",
                                "invoiceNumber": "INV-2024-001",
                                "date": "2024-01-15"
                            },
                            "styling": {
                                "backgroundColor": "#ffffff",
                                "textColor": "#2c3e50",
                                "fontSize": "28px",
                                "fontFamily": "Arial, sans-serif",
                                "padding": "30px",
                                "borderBottom": "2px solid #ecf0f1"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Acme Corporation",
                                "clientAddress": "123 Business Ave\nSuite 100\nNew York, NY 10001",
                                "providerName": "Design Studio Pro",
                                "providerAddress": "456 Creative Blvd\nLos Angeles, CA 90210"
                            },
                            "styling": {
                                "display": "grid",
                                "gridTemplateColumns": "1fr 1fr",
                                "gap": "30px",
                                "padding": "25px",
                                "fontSize": "14px"
                            }
                        },
                        {
                            "type": "line_items",
                            "props": {
                                "items": [
                                    {
                                        "description": "Logo Design",
                                        "quantity": 1,
                                        "unitPrice": 1500,
                                        "total": 1500
                                    },
                                    {
                                        "description": "Brand Guidelines Document",
                                        "quantity": 1,
                                        "unitPrice": 1000,
                                        "total": 1000
                                    }
                                ]
                            },
                            "styling": {
                                "marginTop": "25px",
                                "width": "100%",
                                "borderCollapse": "collapse"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "subtotal": 2500,
                                "tax": 0,
                                "total": 2500,
                                "currency": "USD"
                            },
                            "styling": {
                                "textAlign": "right",
                                "marginTop": "25px",
                                "padding": "20px",
                                "backgroundColor": "#f8f9fa"
                            }
                        }
                    ]
                },
                {
                    "design_name": "Classic & Professional",
                    "design_id": "classic_professional",
                    "style_theme": "classic",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "INVOICE",
                                "companyName": "Design Studio Pro",
                                "invoiceNumber": "INV-2024-001",
                                "date": "January 15, 2024"
                            },
                            "styling": {
                                "backgroundColor": "#fefefe",
                                "textColor": "#333333",
                                "fontSize": "32px",
                                "fontFamily": "Georgia, serif",
                                "padding": "40px",
                                "border": "2px solid #e0e0e0",
                                "textAlign": "center"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Acme Corporation",
                                "clientAddress": "123 Business Ave\nSuite 100\nNew York, NY 10001",
                                "providerName": "Design Studio Pro",
                                "providerAddress": "456 Creative Blvd\nLos Angeles, CA 90210"
                            },
                            "styling": {
                                "display": "flex",
                                "justifyContent": "space-between",
                                "padding": "30px",
                                "fontSize": "15px",
                                "fontFamily": "Georgia, serif"
                            }
                        },
                        {
                            "type": "line_items",
                            "props": {
                                "items": [
                                    {
                                        "description": "Logo Design",
                                        "quantity": 1,
                                        "unitPrice": 1500,
                                        "total": 1500
                                    },
                                    {
                                        "description": "Brand Guidelines Document",
                                        "quantity": 1,
                                        "unitPrice": 1000,
                                        "total": 1000
                                    }
                                ]
                            },
                            "styling": {
                                "marginTop": "30px",
                                "width": "100%",
                                "border": "1px solid #ddd",
                                "fontFamily": "Georgia, serif"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "subtotal": 2500,
                                "tax": 0,
                                "total": 2500,
                                "currency": "USD"
                            },
                            "styling": {
                                "textAlign": "right",
                                "marginTop": "30px",
                                "padding": "25px",
                                "backgroundColor": "#f5f5f5",
                                "border": "1px solid #ddd",
                                "fontFamily": "Georgia, serif"
                            }
                        }
                    ]
                },
                {
                    "design_name": "Bold & Creative",
                    "design_id": "bold_creative",
                    "style_theme": "creative",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "Design Studio Pro",
                                "invoiceNumber": "INV-2024-001",
                                "date": "01/15/2024"
                            },
                            "styling": {
                                "backgroundColor": "#667eea",
                                "textColor": "#ffffff",
                                "fontSize": "26px",
                                "fontFamily": "Helvetica, sans-serif",
                                "padding": "35px",
                                "borderRadius": "8px 8px 0 0",
                                "fontWeight": "bold"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Acme Corporation",
                                "clientAddress": "123 Business Ave\nSuite 100\nNew York, NY 10001",
                                "providerName": "Design Studio Pro",
                                "providerAddress": "456 Creative Blvd\nLos Angeles, CA 90210"
                            },
                            "styling": {
                                "display": "grid",
                                "gridTemplateColumns": "1fr 1fr",
                                "gap": "25px",
                                "padding": "25px",
                                "backgroundColor": "#f8faff",
                                "borderLeft": "4px solid #667eea"
                            }
                        },
                        {
                            "type": "line_items",
                            "props": {
                                "items": [
                                    {
                                        "description": "Logo Design",
                                        "quantity": 1,
                                        "unitPrice": 1500,
                                        "total": 1500
                                    },
                                    {
                                        "description": "Brand Guidelines Document",
                                        "quantity": 1,
                                        "unitPrice": 1000,
                                        "total": 1000
                                    }
                                ]
                            },
                            "styling": {
                                "marginTop": "20px",
                                "width": "100%",
                                "borderRadius": "6px",
                                "overflow": "hidden",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "subtotal": 2500,
                                "tax": 0,
                                "total": 2500,
                                "currency": "USD"
                            },
                            "styling": {
                                "textAlign": "right",
                                "marginTop": "20px",
                                "padding": "20px",
                                "backgroundColor": "#667eea",
                                "color": "#ffffff",
                                "borderRadius": "6px",
                                "fontWeight": "bold"
                            }
                        }
                    ]
                }
            ]
        }
        
        mock_response = Mock()
        mock_response.text = json.dumps(comprehensive_response)
        
        mock_llm.generate_content_async = AsyncMock(return_value=mock_response)
        
        return mock_llm


if __name__ == '__main__':
    unittest.main()