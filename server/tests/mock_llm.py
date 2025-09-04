from typing import Dict, Any, Optional, List, AsyncIterator
import json
import random
from unittest.mock import Mock
from dataclasses import dataclass

@dataclass
class MockGenerateContentResponse:
    """Mock response object that mimics Vertex AI GenerateContentResponse"""
    text: str
    
    def __init__(self, text: str):
        self.text = text
        self._candidates = [MockCandidate(text)]
        self.usage_metadata = MockUsageMetadata(len(text.split()))
    
    @property
    def content(self) -> str:
        """Backward compatibility property for LangChain-style access"""
        return self.text

@dataclass  
class MockCandidate:
    """Mock candidate response"""
    content: 'MockContent'
    
    def __init__(self, text: str):
        self.content = MockContent(text)

@dataclass
class MockContent:
    """Mock content with parts"""
    parts: List['MockPart']
    
    def __init__(self, text: str):
        self.parts = [MockPart(text)]

@dataclass
class MockPart:
    """Mock content part"""
    text: str

@dataclass
class MockUsageMetadata:
    """Mock usage metadata"""
    total_tokens: int

class MockVertexAIModel:
    """Mock Vertex AI GenerativeModel implementation for testing agents without real API calls"""
    
    def __init__(self, response_patterns: Optional[Dict[str, Any]] = None, 
                 simulate_failures: bool = False, failure_rate: float = 0.1, **kwargs):
        """
        Initialize mock LLM with configurable responses
        
        Args:
            response_patterns: Dict mapping input patterns to responses
            simulate_failures: Whether to randomly simulate failures  
            failure_rate: Probability of simulated failures (0.0 to 1.0)
        """
        self.response_patterns = response_patterns or self._default_patterns()
        self.simulate_failures = simulate_failures
        self.failure_rate = failure_rate
        self.call_count = 0
        self.call_history = []
    
    def generate_content(self, prompt: str, **kwargs) -> MockGenerateContentResponse:
        """Mock the generate_content method (synchronous)"""
        return self._generate_response_obj(prompt)
    
    async def generate_content_async(self, prompt: str, **kwargs) -> MockGenerateContentResponse:
        """Mock the generate_content_async method"""
        return self._generate_response_obj(prompt)
    
    def invoke(self, input_text: str, **kwargs) -> MockGenerateContentResponse:
        """Mock invoke method for backward compatibility"""
        return self._generate_response_obj(input_text)
    
    def _generate_response_obj(self, input_text: str, config: Optional[Dict] = None) -> MockGenerateContentResponse:
        """Generate mock response object"""
        self.call_count += 1
        
        # Record call for testing
        call_record = {
            "call_number": self.call_count,
            "input": input_text,
            "config": config,
            "timestamp": "mock_timestamp"
        }
        self.call_history.append(call_record)
        
        # Simulate random failures if enabled
        if self.simulate_failures and random.random() < self.failure_rate:
            raise Exception("Mock LLM failure for testing")
        
        # Find matching response pattern
        response_content = self._generate_response(input_text)
        
        return MockGenerateContentResponse(text=response_content)

    
    def _default_patterns(self) -> Dict[str, Any]:
        """Default response patterns for different agent types"""
        return {
            # Orchestrator decision patterns
            "orchestrator": {
                "contract_data": {
                    "next_action": "validation",
                    "reason": "Contract processed successfully - needs validation",
                    "confidence": 0.9
                },
                "validation_passed": {
                    "next_action": "schedule_extraction", 
                    "reason": "Validation passed - extract schedule data",
                    "confidence": 0.8
                },
                "quality_low": {
                    "next_action": "feedback_learning",
                    "reason": "Low quality score - learn and retry",
                    "confidence": 0.6
                }
            },
            
            # Contract processing patterns
            "contract_processing": {
                "rental_agreement": {
                    "context": "Monthly rent: $1200. Tenant: John Doe. Landlord: ABC Properties. Lease term: 12 months starting January 1, 2024.",
                    "confidence": 0.85,
                    "status": "processed"
                },
                "service_contract": {
                    "context": "Service fee: $500/month. Client: XYZ Corp. Provider: Tech Services Inc. Contract duration: 6 months.",
                    "confidence": 0.80,
                    "status": "processed"
                }
            },
            
            # Invoice generation patterns
            "invoice_generation": {
                "rental": json.dumps({
                    "contract_type": "rental_lease",
                    "client": {"name": "John Doe", "email": "john@email.com"},
                    "service_provider": {"name": "ABC Properties", "email": "abc@properties.com"},
                    "payment_terms": {"amount": 1200, "frequency": "monthly", "currency": "USD"},
                    "services": [{"description": "Monthly rent", "total_amount": 1200}]
                }),
                "service": json.dumps({
                    "contract_type": "service_agreement", 
                    "client": {"name": "XYZ Corp", "email": "contact@xyz.com"},
                    "service_provider": {"name": "Tech Services Inc", "email": "info@techservices.com"},
                    "payment_terms": {"amount": 500, "frequency": "monthly", "currency": "USD"},
                    "services": [{"description": "Technical support services", "total_amount": 500}]
                })
            },
            
            # Schedule extraction patterns
            "schedule_extraction": {
                "monthly": {
                    "frequency": "monthly",
                    "start_date": "2024-01-01",
                    "due_day": 1,
                    "confidence": 0.75
                },
                "quarterly": {
                    "frequency": "quarterly", 
                    "start_date": "2024-01-01",
                    "due_day": 15,
                    "confidence": 0.70
                }
            },
            
            # Invoice design generation patterns
            "invoice_design": {
                "modern_clean": {
                    "design_name": "Modern & Clean",
                    "design_id": "modern_clean",
                    "style_theme": "minimalist",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "{{PROVIDER_NAME}}",
                                "invoiceNumber": "{{INVOICE_NUMBER}}",
                                "date": "{{INVOICE_DATE}}"
                            },
                            "styling": {
                                "backgroundColor": "#ffffff",
                                "textColor": "#2c3e50",
                                "fontSize": "24px",
                                "fontFamily": "Arial, sans-serif",
                                "padding": "20px",
                                "borderBottom": "2px solid #ecf0f1"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "{{CLIENT_NAME}}",
                                "providerName": "{{PROVIDER_NAME}}"
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
                                "items": "{{SERVICE_ITEMS}}"
                            },
                            "styling": {
                                "marginTop": "20px",
                                "width": "100%"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "total": "{{TOTAL_AMOUNT}}",
                                "currency": "{{CURRENCY}}"
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
                "classic_professional": {
                    "design_name": "Classic & Professional", 
                    "design_id": "classic_professional",
                    "style_theme": "classic",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "INVOICE",
                                "companyName": "{{PROVIDER_NAME}}"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif",
                                "fontSize": "28px",
                                "textAlign": "center",
                                "border": "1px solid #ccc"
                            }
                        },
                        {
                            "type": "client_info", 
                            "props": {
                                "clientName": "{{CLIENT_NAME}}",
                                "providerName": "{{PROVIDER_NAME}}"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif",
                                "padding": "25px"
                            }
                        },
                        {
                            "type": "summary",
                            "props": {
                                "total": "{{TOTAL_AMOUNT}}"
                            },
                            "styling": {
                                "fontFamily": "Georgia, serif",
                                "textAlign": "right"
                            }
                        }
                    ]
                },
                "bold_creative": {
                    "design_name": "Bold & Creative",
                    "design_id": "bold_creative", 
                    "style_theme": "creative",
                    "components": [
                        {
                            "type": "header",
                            "props": {
                                "title": "Invoice",
                                "companyName": "{{PROVIDER_NAME}}"
                            },
                            "styling": {
                                "backgroundColor": "#3182ce",
                                "color": "#ffffff",
                                "fontFamily": "Helvetica, sans-serif",
                                "padding": "30px",
                                "borderRadius": "8px"
                            }
                        },
                        {
                            "type": "client_info",
                            "props": {
                                "clientName": "{{CLIENT_NAME}}",
                                "providerName": "{{PROVIDER_NAME}}"
                            },
                            "styling": {
                                "borderLeft": "4px solid #3182ce",
                                "paddingLeft": "20px"
                            }
                        }
                    ]
                },
                "three_designs": {
                    "designs": [
                        {
                            "design_name": "Modern & Clean",
                            "design_id": "modern_clean",
                            "style_theme": "minimalist",
                            "components": [
                                {
                                    "type": "header",
                                    "props": {"title": "Invoice", "companyName": "Service Provider"},
                                    "styling": {"backgroundColor": "#ffffff", "fontFamily": "Arial, sans-serif"}
                                },
                                {
                                    "type": "client_info", 
                                    "props": {"clientName": "Client Name", "providerName": "Provider Name"},
                                    "styling": {"display": "grid", "gridTemplateColumns": "1fr 1fr"}
                                },
                                {
                                    "type": "line_items",
                                    "props": {"items": []},
                                    "styling": {"width": "100%"}
                                },
                                {
                                    "type": "summary",
                                    "props": {"total": 1000, "currency": "USD"},
                                    "styling": {"textAlign": "right"}
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
                                    "props": {"title": "INVOICE", "companyName": "Service Provider"},
                                    "styling": {"fontFamily": "Georgia, serif", "textAlign": "center"}
                                },
                                {
                                    "type": "client_info",
                                    "props": {"clientName": "Client Name", "providerName": "Provider Name"},
                                    "styling": {"fontFamily": "Georgia, serif"}
                                },
                                {
                                    "type": "summary", 
                                    "props": {"total": 1000, "currency": "USD"},
                                    "styling": {"fontFamily": "Georgia, serif", "textAlign": "right"}
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
                                    "props": {"title": "Invoice", "companyName": "Service Provider"},
                                    "styling": {"backgroundColor": "#3182ce", "color": "#ffffff"}
                                },
                                {
                                    "type": "client_info",
                                    "props": {"clientName": "Client Name", "providerName": "Provider Name"},
                                    "styling": {"borderLeft": "4px solid #3182ce"}
                                }
                            ]
                        }
                    ]
                }
            }
        }
    
    def _generate_response(self, input_text: str) -> str:
        """Generate appropriate response based on input patterns"""
        input_lower = input_text.lower()
        
        # Orchestrator responses
        if "orchestrator" in input_lower or "next_action" in input_lower:
            if "contract_data" in input_lower and "validation_results" not in input_lower:
                return json.dumps(self.response_patterns["orchestrator"]["contract_data"])
            elif "validation_results" in input_lower and "passed" in input_lower:
                return json.dumps(self.response_patterns["orchestrator"]["validation_passed"])  
            elif "quality_score" in input_lower and any(word in input_lower for word in ["low", "0.5", "0.4"]):
                return json.dumps(self.response_patterns["orchestrator"]["quality_low"])
        
        # Contract processing responses
        if "extract" in input_lower and "contract" in input_lower:
            if "rental" in input_lower or "rent" in input_lower:
                return json.dumps(self.response_patterns["contract_processing"]["rental_agreement"])
            else:
                return json.dumps(self.response_patterns["contract_processing"]["service_contract"])
        
        # Invoice generation responses
        if "json" in input_lower and ("invoice" in input_lower or "billing" in input_lower):
            if "rental" in input_lower or "rent" in input_lower:
                return self.response_patterns["invoice_generation"]["rental"]
            else:
                return self.response_patterns["invoice_generation"]["service"]
        
        # Schedule extraction responses
        if "schedule" in input_lower or "frequency" in input_lower:
            if "monthly" in input_lower:
                return json.dumps(self.response_patterns["schedule_extraction"]["monthly"])
            else:
                return json.dumps(self.response_patterns["schedule_extraction"]["quarterly"])
        
        # Invoice design generation responses
        if "design" in input_lower and ("ui" in input_lower or "invoice" in input_lower):
            if "3 different" in input_text or "three designs" in input_lower:
                return json.dumps(self.response_patterns["invoice_design"]["three_designs"])
            elif "modern" in input_lower and "clean" in input_lower:
                return json.dumps({"designs": [self.response_patterns["invoice_design"]["modern_clean"]]})
            elif "classic" in input_lower and "professional" in input_lower:
                return json.dumps({"designs": [self.response_patterns["invoice_design"]["classic_professional"]]})
            elif "bold" in input_lower and "creative" in input_lower:
                return json.dumps({"designs": [self.response_patterns["invoice_design"]["bold_creative"]]})
            else:
                # Default to three designs for any design request
                return json.dumps(self.response_patterns["invoice_design"]["three_designs"])
        
        # Default response
        return json.dumps({
            "status": "mock_response",
            "message": "Mock LLM response for testing",
            "confidence": 0.7,
            "input_received": input_text[:100] + "..." if len(input_text) > 100 else input_text
        })
    
    def _calculate_confidence(self, input_text: str) -> float:
        """Calculate mock confidence based on input quality"""
        if len(input_text) < 20:
            return random.uniform(0.2, 0.5)
        elif len(input_text) < 100:
            return random.uniform(0.5, 0.7)
        else:
            return random.uniform(0.7, 0.9)
    
    def get_call_count(self) -> int:
        """Get number of times the mock LLM was called"""
        return self.call_count
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of all LLM calls"""
        return self.call_history
    
    def reset_calls(self) -> None:
        """Reset call counter and history"""
        self.call_count = 0
        self.call_history = []


class MockLLMFactory:
    """Factory for creating different types of mock Vertex AI models"""
    
    @staticmethod
    def create_reliable_llm() -> MockVertexAIModel:
        """Create a reliable mock Vertex AI model that never fails"""
        return MockVertexAIModel(simulate_failures=False)
    
    @staticmethod  
    def create_unreliable_llm(failure_rate: float = 0.3) -> MockVertexAIModel:
        """Create an unreliable mock Vertex AI model for testing error handling"""
        return MockVertexAIModel(simulate_failures=True, failure_rate=failure_rate)
    
    @staticmethod
    def create_custom_llm(response_patterns: Dict[str, Any]) -> MockVertexAIModel:
        """Create mock Vertex AI model with custom response patterns"""
        return MockVertexAIModel(response_patterns=response_patterns)


def create_mock_model_function():
    """Create a mock get_model function for testing"""
    mock_model = MockLLMFactory.create_reliable_llm()
    
    def mock_get_model(*args, **kwargs):
        return mock_model
    
    return mock_model, mock_get_model