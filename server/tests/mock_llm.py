from typing import Dict, Any, Optional, List, AsyncIterator
import json
import random
from unittest.mock import Mock
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain_core.outputs import LLMResult, Generation

class MockLLMResponse:
    """Mock response object that mimics LangChain LLM response"""
    
    def __init__(self, content: str, confidence: float = 0.8):
        self.content = content
        self.confidence = confidence
        self.usage_metadata = {"total_tokens": len(content.split())}

class MockLLM(BaseLanguageModel):
    """Mock LLM implementation for testing agents without real API calls"""
    
    def __init__(self, response_patterns: Optional[Dict[str, Any]] = None, 
                 simulate_failures: bool = False, failure_rate: float = 0.1, **kwargs):
        """
        Initialize mock LLM with configurable responses
        
        Args:
            response_patterns: Dict mapping input patterns to responses
            simulate_failures: Whether to randomly simulate failures  
            failure_rate: Probability of simulated failures (0.0 to 1.0)
        """
        super().__init__(**kwargs)
        # Use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'response_patterns', response_patterns or self._default_patterns())
        object.__setattr__(self, 'simulate_failures', simulate_failures)
        object.__setattr__(self, 'failure_rate', failure_rate)
        object.__setattr__(self, 'call_count', 0)
        object.__setattr__(self, 'call_history', [])
    
    def invoke(self, input_text: str, config: Optional[Dict] = None) -> MockLLMResponse:
        """Mock the invoke method"""
        object.__setattr__(self, 'call_count', self.call_count + 1)
        
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
        confidence = self._calculate_confidence(input_text)
        
        return MockLLMResponse(content=response_content, confidence=confidence)

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, 
                  run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> LLMResult:
        """Generate responses for multiple prompts"""
        generations = []
        for prompt in prompts:
            response = self.invoke(prompt)
            generations.append([Generation(text=response.content)])
        return LLMResult(generations=generations)

    async def _agenerate(self, prompts: List[str], stop: Optional[List[str]] = None,
                        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None, **kwargs: Any) -> LLMResult:
        """Async generate responses for multiple prompts"""
        return self._generate(prompts, stop, None, **kwargs)

    def predict(self, text: str, **kwargs: Any) -> str:
        """Predict method for compatibility"""
        response = self.invoke(text)
        return response.content

    def predict_messages(self, messages: List[BaseMessage], **kwargs: Any) -> BaseMessage:
        """Predict messages method for compatibility"""
        if messages:
            text = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            response = self.invoke(str(text))
            return AIMessage(content=response.content)
        return AIMessage(content="Empty message list")

    async def apredict(self, text: str, **kwargs: Any) -> str:
        """Async predict method"""
        return self.predict(text, **kwargs)

    async def apredict_messages(self, messages: List[BaseMessage], **kwargs: Any) -> BaseMessage:
        """Async predict messages method"""
        return self.predict_messages(messages, **kwargs)

    def generate_prompt(self, prompts, **kwargs: Any) -> LLMResult:
        """Generate from prompt objects"""
        prompt_strings = [str(p) for p in prompts]
        return self._generate(prompt_strings, **kwargs)

    async def agenerate_prompt(self, prompts, **kwargs: Any) -> LLMResult:
        """Async generate from prompt objects"""
        return self.generate_prompt(prompts, **kwargs)

    @property
    def _llm_type(self) -> str:
        """Return type of language model."""
        return "mock_llm"
    
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
        object.__setattr__(self, 'call_count', 0)
        object.__setattr__(self, 'call_history', [])


class MockLLMFactory:
    """Factory for creating different types of mock LLMs"""
    
    @staticmethod
    def create_reliable_llm() -> MockLLM:
        """Create a reliable mock LLM that never fails"""
        return MockLLM(simulate_failures=False)
    
    @staticmethod  
    def create_unreliable_llm(failure_rate: float = 0.3) -> MockLLM:
        """Create an unreliable mock LLM for testing error handling"""
        return MockLLM(simulate_failures=True, failure_rate=failure_rate)
    
    @staticmethod
    def create_custom_llm(response_patterns: Dict[str, Any]) -> MockLLM:
        """Create mock LLM with custom response patterns"""
        return MockLLM(response_patterns=response_patterns)


def create_mock_model_function():
    """Create a mock get_model function for testing"""
    mock_llm = MockLLMFactory.create_reliable_llm()
    
    def mock_get_model():
        return mock_llm
    
    return mock_llm, mock_get_model