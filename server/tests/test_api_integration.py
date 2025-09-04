#!/usr/bin/env python3
"""
API Integration tests for invoice design endpoints

Tests the new adaptive UI designs API endpoint with various scenarios
and error conditions.
"""

import os
import sys
import unittest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from fastapi.testclient import TestClient
    from fastapi import HTTPException
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️  FastAPI TestClient not available - skipping API integration tests")


class TestInvoiceDesignAPI(unittest.TestCase):
    """Test cases for invoice design API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI TestClient not available")
        
        # Mock invoice data for testing
        self.sample_invoice_data = {
            "invoice_header": {
                "invoice_number": "INV-API-001",
                "invoice_date": "2024-01-15"
            },
            "parties": {
                "client": {
                    "name": "API Test Client",
                    "email": "client@apitest.com"
                },
                "service_provider": {
                    "name": "API Test Provider",
                    "email": "provider@apitest.com"
                }
            },
            "payment_terms": {
                "amount": 2000,
                "currency": "USD"
            },
            "contract_title": "API Testing Services"
        }
        
        # Mock designs data
        self.sample_designs = {
            "designs": [
                {
                    "design_name": "Modern & Clean",
                    "design_id": "modern_clean",
                    "style_theme": "minimalist",
                    "components": [
                        {
                            "type": "header",
                            "props": {"title": "Invoice", "companyName": "API Test Provider"},
                            "styling": {"backgroundColor": "#ffffff"}
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
                            "props": {"title": "INVOICE", "companyName": "API Test Provider"},
                            "styling": {"fontFamily": "Georgia, serif"}
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
                            "props": {"title": "Invoice", "companyName": "API Test Provider"},
                            "styling": {"backgroundColor": "#3182ce"}
                        }
                    ]
                }
            ]
        }
    
    def test_get_adaptive_ui_designs_success(self):
        """Test successful retrieval of adaptive UI designs"""
        with patch('routes.invoices.get_database_service') as mock_db_service:
            # Setup mock database response
            mock_db = Mock()
            mock_invoice = Mock()
            mock_invoice.id = "test-invoice-123"
            mock_invoice.invoice_number = "INV-API-001"
            mock_invoice.workflow_id = "test-workflow"
            mock_invoice.client_name = "API Test Client"
            mock_invoice.service_provider_name = "API Test Provider"
            
            # Mock invoice data with adaptive designs
            invoice_data_with_designs = self.sample_invoice_data.copy()
            invoice_data_with_designs['adaptive_ui_designs'] = self.sample_designs
            mock_invoice.invoice_data = invoice_data_with_designs
            
            mock_db.get_invoice_by_id.return_value = mock_invoice
            mock_db_service.return_value = mock_db
            
            # Import app after mocking
            from main import app
            client = TestClient(app)
            
            # Test the endpoint
            response = client.get("/api/v1/invoices/test-invoice-123/adaptive-ui-designs")
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertEqual(data["invoice_id"], "test-invoice-123")
            self.assertEqual(data["invoice_number"], "INV-API-001")
            self.assertEqual(data["workflow_id"], "test-workflow")
            self.assertEqual(len(data["designs"]), 3)
            self.assertEqual(data["total_designs"], 3)
            
            # Verify design names
            design_names = [design["design_name"] for design in data["designs"]]
            self.assertIn("Modern & Clean", design_names)
            self.assertIn("Classic & Professional", design_names)
            self.assertIn("Bold & Creative", design_names)
    
    def test_get_adaptive_ui_designs_invoice_not_found(self):
        """Test handling when invoice is not found"""
        with patch('routes.invoices.get_database_service') as mock_db_service:
            # Setup mock to return None (invoice not found)
            mock_db = Mock()
            mock_db.get_invoice_by_id.return_value = None
            mock_db_service.return_value = mock_db
            
            # Import app after mocking
            from main import app
            client = TestClient(app)
            
            # Test the endpoint
            response = client.get("/api/v1/invoices/nonexistent-invoice/adaptive-ui-designs")
            
            # Verify 404 response
            self.assertEqual(response.status_code, 404)
            
            data = response.json()
            self.assertIn("Invoice not found", data["detail"])
    
    def test_get_adaptive_ui_designs_no_designs(self):
        """Test handling when invoice has no adaptive designs"""
        with patch('routes.invoices.get_database_service') as mock_db_service:
            # Setup mock with invoice but no designs
            mock_db = Mock()
            mock_invoice = Mock()
            mock_invoice.id = "test-invoice-456"
            mock_invoice.invoice_number = "INV-NO-DESIGNS"
            mock_invoice.client_name = "Test Client"
            mock_invoice.service_provider_name = "Test Provider"
            mock_invoice.invoice_data = self.sample_invoice_data  # No adaptive_ui_designs key
            
            mock_db.get_invoice_by_id.return_value = mock_invoice
            mock_db_service.return_value = mock_db
            
            # Import app after mocking
            from main import app
            client = TestClient(app)
            
            # Test the endpoint
            response = client.get("/api/v1/invoices/test-invoice-456/adaptive-ui-designs")
            
            # Verify successful response with empty designs
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertEqual(data["invoice_id"], "test-invoice-456")
            self.assertEqual(len(data["designs"]), 0)
            self.assertIn("No adaptive UI designs found", data["message"])
    
    def test_get_adaptive_ui_designs_database_error(self):
        """Test handling of database errors"""
        with patch('routes.invoices.get_database_service') as mock_db_service:
            # Setup mock to raise exception
            mock_db = Mock()
            mock_db.get_invoice_by_id.side_effect = Exception("Database connection error")
            mock_db_service.return_value = mock_db
            
            # Import app after mocking
            from main import app
            client = TestClient(app)
            
            # Test the endpoint
            response = client.get("/api/v1/invoices/test-invoice/adaptive-ui-designs")
            
            # Verify 500 response
            self.assertEqual(response.status_code, 500)
            
            data = response.json()
            self.assertIn("Error fetching adaptive UI designs", data["detail"])
    
    def test_get_adaptive_ui_designs_invalid_invoice_id_format(self):
        """Test handling of various invoice ID formats"""
        with patch('routes.invoices.get_database_service') as mock_db_service:
            # Setup basic mock
            mock_db = Mock()
            mock_db.get_invoice_by_id.return_value = None  # Not found for any ID
            mock_db_service.return_value = mock_db
            
            # Import app after mocking
            from main import app
            client = TestClient(app)
            
            # Test various ID formats
            test_ids = [
                "123",
                "invoice-123",
                "inv_abc_123",
                "very-long-invoice-id-with-many-characters-and-numbers-123456789",
                "inv with spaces"
            ]
            
            for invoice_id in test_ids:
                response = client.get(f"/api/v1/invoices/{invoice_id}/adaptive-ui-designs")
                
                # Should handle all formats gracefully, even if invoice not found
                self.assertEqual(response.status_code, 404)
                data = response.json()
                self.assertIn("Invoice not found", data["detail"])
    
    def test_get_adaptive_ui_designs_malformed_designs_data(self):
        """Test handling of malformed designs data in database"""
        with patch('routes.invoices.get_database_service') as mock_db_service:
            # Setup mock with malformed designs data
            mock_db = Mock()
            mock_invoice = Mock()
            mock_invoice.id = "test-invoice-malformed"
            mock_invoice.invoice_number = "INV-MALFORMED"
            mock_invoice.client_name = "Test Client"
            mock_invoice.service_provider_name = "Test Provider"
            
            # Malformed designs data
            invoice_data_malformed = self.sample_invoice_data.copy()
            invoice_data_malformed['adaptive_ui_designs'] = {
                "invalid_key": "invalid_data",
                "designs": "not_an_array"  # Should be an array
            }
            mock_invoice.invoice_data = invoice_data_malformed
            
            mock_db.get_invoice_by_id.return_value = mock_invoice
            mock_db_service.return_value = mock_db
            
            # Import app after mocking
            from main import app
            client = TestClient(app)
            
            # Test the endpoint
            response = client.get("/api/v1/invoices/test-invoice-malformed/adaptive-ui-designs")
            
            # Should handle gracefully and return empty designs
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertEqual(data["invoice_id"], "test-invoice-malformed")
            self.assertEqual(len(data["designs"]), 0)


class TestInvoiceDesignAPIIntegration(unittest.TestCase):
    """Integration tests for invoice design API with real-like scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI TestClient not available")
        
        # Comprehensive invoice data for integration testing
        self.comprehensive_invoice = {
            "invoice_header": {
                "invoice_number": "INV-INTEGRATION-001",
                "invoice_date": "2024-01-15",
                "due_date": "2024-02-15"
            },
            "parties": {
                "client": {
                    "name": "Integration Test Corp",
                    "email": "billing@integration.com",
                    "address": "123 Integration Ave\nTest City, TC 12345"
                },
                "service_provider": {
                    "name": "Professional Services LLC",
                    "email": "invoices@professional.com",
                    "address": "456 Service Blvd\nProvider City, PC 67890"
                }
            },
            "payment_terms": {
                "amount": 15000,
                "currency": "USD",
                "frequency": "quarterly"
            },
            "contract_title": "Enterprise Software Development Services",
            "services": [
                {
                    "description": "Full-Stack Development",
                    "quantity": 1,
                    "unit_price": 10000,
                    "total_amount": 10000
                },
                {
                    "description": "DevOps Setup",
                    "quantity": 1,
                    "unit_price": 5000,
                    "total_amount": 5000
                }
            ]
        }
        
        # Comprehensive designs with all component types
        self.comprehensive_designs = {
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
                                "companyName": "Professional Services LLC",
                                "invoiceNumber": "INV-INTEGRATION-001",
                                "date": "2024-01-15"
                            },
                            "styling": {
                                "backgroundColor": "#ffffff",
                                "fontFamily": "Arial, sans-serif",
                                "fontSize": "24px",
                                "padding": "20px"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Integration Test Corp",
                                "clientAddress": "123 Integration Ave\nTest City, TC 12345",
                                "providerName": "Professional Services LLC",
                                "providerAddress": "456 Service Blvd\nProvider City, PC 67890"
                            },
                            "styling": {
                                "display": "grid",
                                "gridTemplateColumns": "1fr 1fr",
                                "gap": "20px",
                                "padding": "20px"
                            }
                        },
                        {
                            "type": "line_items",
                            "props": {
                                "items": [
                                    {
                                        "description": "Full-Stack Development",
                                        "quantity": 1,
                                        "unitPrice": 10000,
                                        "total": 10000
                                    },
                                    {
                                        "description": "DevOps Setup",
                                        "quantity": 1,
                                        "unitPrice": 5000,
                                        "total": 5000
                                    }
                                ]
                            },
                            "styling": {
                                "width": "100%",
                                "marginTop": "20px"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "subtotal": 15000,
                                "tax": 0,
                                "total": 15000,
                                "currency": "USD"
                            },
                            "styling": {
                                "textAlign": "right",
                                "marginTop": "20px",
                                "padding": "15px",
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
                                "companyName": "Professional Services LLC",
                                "invoiceNumber": "INV-INTEGRATION-001"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif",
                                "fontSize": "28px",
                                "textAlign": "center",
                                "border": "1px solid #ccc",
                                "padding": "25px"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Integration Test Corp",
                                "providerName": "Professional Services LLC"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif",
                                "padding": "25px",
                                "display": "flex",
                                "justifyContent": "space-between"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "total": 15000,
                                "currency": "USD"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif",
                                "textAlign": "right",
                                "padding": "25px",
                                "backgroundColor": "#f5f5f5"
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
                                "companyName": "Professional Services LLC"
                            },
                            "styling": {
                                "backgroundColor": "#667eea",
                                "color": "#ffffff",
                                "fontFamily": "Helvetica, sans-serif",
                                "padding": "30px",
                                "borderRadius": "8px"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "Integration Test Corp",
                                "providerName": "Professional Services LLC"
                            },
                            "styling": {
                                "borderLeft": "4px solid #667eea",
                                "paddingLeft": "20px",
                                "backgroundColor": "#f8faff"
                            }
                        }
                    ]
                }
            ],
            "generated_at": "2024-01-15T10:30:00Z"
        }
    
    def test_comprehensive_api_integration(self):
        """Test comprehensive API integration with full data"""
        with patch('routes.invoices.get_database_service') as mock_db_service:
            # Setup comprehensive mock
            mock_db = Mock()
            mock_invoice = Mock()
            mock_invoice.id = "integration-test-invoice"
            mock_invoice.invoice_number = "INV-INTEGRATION-001"
            mock_invoice.workflow_id = "integration-workflow"
            mock_invoice.client_name = "Integration Test Corp"
            mock_invoice.service_provider_name = "Professional Services LLC"
            
            # Include comprehensive designs
            invoice_data_with_designs = self.comprehensive_invoice.copy()
            invoice_data_with_designs['adaptive_ui_designs'] = self.comprehensive_designs
            mock_invoice.invoice_data = invoice_data_with_designs
            
            mock_db.get_invoice_by_id.return_value = mock_invoice
            mock_db_service.return_value = mock_db
            
            # Import app after mocking
            from main import app
            client = TestClient(app)
            
            # Test the endpoint
            response = client.get("/api/v1/invoices/integration-test-invoice/adaptive-ui-designs")
            
            # Comprehensive verification
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            # Verify basic invoice info
            self.assertEqual(data["invoice_id"], "integration-test-invoice")
            self.assertEqual(data["invoice_number"], "INV-INTEGRATION-001")
            self.assertEqual(data["client_name"], "Integration Test Corp")
            self.assertEqual(data["service_provider_name"], "Professional Services LLC")
            
            # Verify designs structure
            self.assertEqual(len(data["designs"]), 3)
            self.assertEqual(data["total_designs"], 3)
            self.assertIn("generated_at", data)
            
            # Verify each design
            designs_by_name = {design["design_name"]: design for design in data["designs"]}
            
            # Modern & Clean verification
            modern_design = designs_by_name["Modern & Clean"]
            self.assertEqual(modern_design["style_theme"], "minimalist")
            self.assertTrue(len(modern_design["components"]) >= 4)  # header, client_info, line_items, summary
            
            # Classic & Professional verification
            classic_design = designs_by_name["Classic & Professional"]
            self.assertEqual(classic_design["style_theme"], "classic")
            
            # Bold & Creative verification
            creative_design = designs_by_name["Bold & Creative"]
            self.assertEqual(creative_design["style_theme"], "creative")
            
            # Verify component structure for Modern design
            component_types = [comp["type"] for comp in modern_design["components"]]
            self.assertIn("header", component_types)
            self.assertIn("client_info", component_types)
            self.assertIn("line_items", component_types)
            self.assertIn("summary", component_types)
            
            # Verify header component details
            header_component = next(comp for comp in modern_design["components"] if comp["type"] == "header")
            self.assertIn("title", header_component["props"])
            self.assertIn("companyName", header_component["props"])
            self.assertIn("styling", header_component)
            
    def test_api_response_structure_validation(self):
        """Test that API response follows expected structure"""
        with patch('routes.invoices.get_database_service') as mock_db_service:
            # Setup mock
            mock_db = Mock()
            mock_invoice = Mock()
            mock_invoice.id = "structure-test-invoice"
            mock_invoice.invoice_number = "INV-STRUCT-001"
            mock_invoice.workflow_id = "struct-workflow"
            mock_invoice.client_name = "Structure Test Client"
            mock_invoice.service_provider_name = "Structure Test Provider"
            
            invoice_data_with_designs = self.comprehensive_invoice.copy()
            invoice_data_with_designs['adaptive_ui_designs'] = self.comprehensive_designs
            mock_invoice.invoice_data = invoice_data_with_designs
            
            mock_db.get_invoice_by_id.return_value = mock_invoice
            mock_db_service.return_value = mock_db
            
            # Import app after mocking
            from main import app
            client = TestClient(app)
            
            # Test the endpoint
            response = client.get("/api/v1/invoices/structure-test-invoice/adaptive-ui-designs")
            
            # Verify response structure
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Required top-level fields
            required_fields = [
                "invoice_id", "invoice_number", "workflow_id", "client_name", 
                "service_provider_name", "designs", "total_designs"
            ]
            
            for field in required_fields:
                self.assertIn(field, data, f"Required field '{field}' missing from response")
            
            # Verify designs structure
            self.assertIsInstance(data["designs"], list)
            self.assertGreater(len(data["designs"]), 0)
            
            # Verify each design structure
            for design in data["designs"]:
                design_required_fields = ["design_name", "design_id", "style_theme", "components"]
                for field in design_required_fields:
                    self.assertIn(field, design, f"Design missing required field '{field}'")
                
                # Verify components structure
                self.assertIsInstance(design["components"], list)
                for component in design["components"]:
                    component_required_fields = ["type", "props", "styling"]
                    for field in component_required_fields:
                        self.assertIn(field, component, f"Component missing required field '{field}'")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)