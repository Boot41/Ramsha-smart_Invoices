from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime
from .base_agent import BaseAgent
from schemas.workflow_schemas import WorkflowState, AgentType, ProcessingStatus
from models.llm.base import get_model
from services.database_service import get_database_service

logger = logging.getLogger(__name__)

class InvoiceDesignAgent(BaseAgent):
    """Agent responsible for generating multiple adaptive UI designs for invoices using LLM"""
    
    def __init__(self):
        super().__init__(AgentType.INVOICE_DESIGN)
        self.model = get_model("gemini-2.0-flash", temperature=0.3, max_output_tokens=8000)
        self.db_service = get_database_service()
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """
        Generate multiple invoice UI designs from contract data
        
        Args:
            state: Current workflow state containing validated contract data
            
        Returns:
            Updated workflow state with generated UI designs
        """
        workflow_id = state.get('workflow_id')
        self.logger.info(f"🎨 Starting invoice design generation for workflow_id: {workflow_id}")
        
        try:
            # Extract invoice data - prioritize database invoice data
            invoice_data = await self._extract_invoice_data_from_database(state)
            
            if not invoice_data:
                raise ValueError("No invoice data found in database for design generation")
            
            # Generate 3 different UI designs using LLM
            designs = await self.generate_designs(invoice_data)
            
            if not designs or not designs.get("designs"):
                raise ValueError("Failed to generate invoice designs")
            
            # Store designs in database and state
            await self._save_designs_to_database(state, designs)
            
            # Store designs in state
            state["invoice_designs"] = designs
            state["design_generation_completed"] = True
            state["design_generation_timestamp"] = datetime.now().isoformat()
            
            # Update processing status
            state["processing_status"] = ProcessingStatus.SUCCESS.value
            
            # Update metrics
            self.update_state_metrics(
                state,
                confidence=0.85,
                quality_score=0.9
            )
            
            self.logger.info(f"✅ Generated {len(designs['designs'])} invoice designs for workflow {workflow_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Invoice design generation failed for workflow {workflow_id}: {str(e)}")
            
            # Update state with error
            state["processing_status"] = ProcessingStatus.FAILED.value
            state["design_generation_completed"] = False
            
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "invoice_design",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return state
    
    async def generate_designs(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate 3 different invoice UI designs using LLM
        
        Args:
            contract_data: The contract/invoice data to base designs on
            
        Returns:
            Dictionary containing array of 3 UI design definitions
        """
        try:
            # Create the prompt for LLM
            prompt = self._create_design_prompt(contract_data)
            
            # Generate designs using Gemini
            response = await self.model.generate_content_async(prompt)
            response_text = response.text
            
            # Parse and validate the response
            designs = self._parse_design_response(response_text)
            
            return designs
            
        except Exception as e:
            self.logger.error(f"❌ Error generating designs with LLM: {str(e)}")
            raise Exception(f"Failed to generate invoice designs: {str(e)}")
    
    def _create_design_prompt(self, contract_data: Dict[str, Any]) -> str:
        """Create the sophisticated prompt for generating invoice designs"""
        
        # Extract key information from contract data
        client_name = self._safe_get(contract_data, "client.name", "CLIENT_NAME")
        service_provider_name = self._safe_get(contract_data, "service_provider.name", "SERVICE_PROVIDER")
        contract_title = contract_data.get("contract_title", "CONTRACT_TITLE")
        payment_amount = self._safe_get(contract_data, "payment_terms.amount", 0)
        currency = self._safe_get(contract_data, "payment_terms.currency", "USD")
        
        prompt = f"""You are an expert UI designer creating a portfolio of invoice designs. For the provided contract data, generate a JSON object that contains an array of 3 different UI definitions.

Each UI definition in the array must follow the established JSON structure and have a unique design_name.

1. Design 1: Name it "Modern & Clean". Use a minimalist layout, generous whitespace, and a sans-serif font.
2. Design 2: Name it "Classic & Professional". Use a more traditional layout, perhaps with a serif font and a formal structure.
3. Design 3: Name it "Bold & Creative". Use a strong brand color, unique typography, and a more unconventional layout.

Here is the invoice data: {json.dumps(contract_data, indent=2)}

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON, no additional text or markdown
- Each design must include a complete component structure with header, line items, and summary
- Use realistic styling properties (colors, fonts, spacing)
- Include responsive design considerations
- Make each design visually distinct from the others

JSON STRUCTURE EXAMPLE:
{{
  "designs": [
    {{
      "design_name": "Modern & Clean",
      "design_id": "modern_clean",
      "style_theme": "minimalist",
      "components": [
        {{
          "type": "header",
          "props": {{
            "title": "Invoice",
            "companyName": "{service_provider_name}",
            "invoiceNumber": "INV-001",
            "date": "2024-01-15"
          }},
          "styling": {{
            "backgroundColor": "#ffffff",
            "textColor": "#2c3e50",
            "fontSize": "24px",
            "fontFamily": "Arial, sans-serif",
            "padding": "20px",
            "borderBottom": "2px solid #ecf0f1"
          }}
        }},
        {{
          "type": "client_info",
          "props": {{
            "clientName": "{client_name}",
            "clientAddress": "Client Address",
            "providerName": "{service_provider_name}",
            "providerAddress": "Provider Address"
          }},
          "styling": {{
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr",
            "gap": "20px",
            "padding": "20px",
            "fontSize": "14px"
          }}
        }},
        {{
          "type": "line_items",
          "props": {{
            "items": [
              {{
                "description": "{contract_title}",
                "quantity": 1,
                "unitPrice": {payment_amount},
                "total": {payment_amount}
              }}
            ]
          }},
          "styling": {{
            "marginTop": "20px",
            "borderCollapse": "collapse",
            "width": "100%"
          }}
        }},
        {{
          "type": "summary",
          "props": {{
            "subtotal": {payment_amount},
            "tax": 0,
            "total": {payment_amount},
            "currency": "{currency}"
          }},
          "styling": {{
            "textAlign": "right",
            "marginTop": "20px",
            "padding": "15px",
            "backgroundColor": "#f8f9fa"
          }}
        }}
      ]
    }}
  ]
}}

Generate exactly 3 designs following this structure. Ensure each design has a unique visual identity while maintaining professional invoice standards.

Return only the JSON object, no additional text."""

        return prompt
    
    def _parse_design_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate the LLM response containing the designs"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Remove any markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            designs = json.loads(response_text)
            
            # Validate structure
            if not isinstance(designs, dict) or "designs" not in designs:
                raise ValueError("Response does not contain 'designs' key")
            
            if not isinstance(designs["designs"], list):
                raise ValueError("'designs' must be an array")
            
            if len(designs["designs"]) != 3:
                self.logger.warning(f"Expected 3 designs, got {len(designs['designs'])}")
            
            # Validate each design has required fields
            for i, design in enumerate(designs["designs"]):
                if not isinstance(design, dict):
                    raise ValueError(f"Design {i} is not a valid object")
                
                required_fields = ["design_name", "components"]
                for field in required_fields:
                    if field not in design:
                        raise ValueError(f"Design {i} missing required field: {field}")
                
                if not isinstance(design["components"], list):
                    raise ValueError(f"Design {i} components must be an array")
            
            self.logger.info(f"✅ Successfully parsed {len(designs['designs'])} designs")
            return designs
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON parsing error: {str(e)}")
            self.logger.error(f"Raw response: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            self.logger.error(f"❌ Error parsing design response: {str(e)}")
            raise ValueError(f"Failed to parse design response: {str(e)}")
    
    async def _extract_invoice_data_from_database(self, state: WorkflowState) -> Optional[Dict[str, Any]]:
        """Extract invoice data from database using workflow_id or invoice_id"""
        
        # First try to get invoice by invoice_id if available
        invoice_id = state.get("invoice_id")
        if invoice_id:
            try:
                invoice_record = await self.db_service.get_invoice_by_id(invoice_id)
                if invoice_record and invoice_record.invoice_data:
                    self.logger.info(f"✅ Retrieved invoice data from database using invoice_id: {invoice_id}")
                    return invoice_record.invoice_data
            except Exception as e:
                self.logger.warning(f"Failed to retrieve invoice by ID: {str(e)}")
        
        # Try to get by workflow_id
        workflow_id = state.get("workflow_id")
        if workflow_id:
            try:
                invoice_record = await self.db_service.get_invoice_by_workflow_id(workflow_id)
                if invoice_record and invoice_record.invoice_data:
                    self.logger.info(f"✅ Retrieved invoice data from database using workflow_id: {workflow_id}")
                    return invoice_record.invoice_data
            except Exception as e:
                self.logger.warning(f"Failed to retrieve invoice by workflow_id: {str(e)}")
        
        # Fallback to state data if database lookup fails
        self.logger.warning("Could not retrieve invoice data from database, checking state...")
        
        # Try final corrected invoice data from state as fallback
        if state.get("final_invoice"):
            self.logger.debug("Using final corrected invoice data from state as fallback")
            return state["final_invoice"]
        
        # Try validated invoice data from state
        if state.get("invoice_data"):
            invoice_data = state["invoice_data"]
            if isinstance(invoice_data, dict):
                # Check for nested structures
                if "invoice_response" in invoice_data:
                    if isinstance(invoice_data["invoice_response"], dict) and "invoice_data" in invoice_data["invoice_response"]:
                        self.logger.debug("Using nested invoice data from state")
                        return invoice_data["invoice_response"]["invoice_data"]
                
                self.logger.debug("Using root invoice data from state")
                return invoice_data
        
        # Try contract data as final fallback
        if state.get("contract_data"):
            self.logger.debug("Using contract data from state as final fallback")
            return state["contract_data"]
        
        self.logger.error("No invoice data found in database or state")
        return None
    
    async def _save_designs_to_database(self, state: WorkflowState, designs: Dict[str, Any]) -> bool:
        """Save generated designs to database for later retrieval"""
        try:
            # Get invoice record to save designs to
            invoice_record = None
            invoice_id = state.get("invoice_id")
            workflow_id = state.get("workflow_id")
            
            if invoice_id:
                invoice_record = await self.db_service.get_invoice_by_id(invoice_id)
            elif workflow_id:
                invoice_record = await self.db_service.get_invoice_by_workflow_id(workflow_id)
            
            if not invoice_record:
                self.logger.warning("No invoice record found to save designs to")
                return False
            
            # Update the invoice record with designs - we'll add a new field to store designs
            # For now, we can store it in the invoice_data field under a designs key
            if hasattr(invoice_record, 'invoice_data') and invoice_record.invoice_data:
                # Add designs to existing invoice_data
                updated_invoice_data = invoice_record.invoice_data.copy()
                updated_invoice_data['adaptive_ui_designs'] = designs
                
                # Update the database record
                from sqlalchemy import update
                async with self.db_service.get_session() as session:
                    stmt = update(self.db_service.Invoice.__table__).where(
                        self.db_service.Invoice.id == invoice_record.id
                    ).values(
                        invoice_data=updated_invoice_data
                    )
                    await session.execute(stmt)
                    await session.commit()
                
                self.logger.info(f"✅ Saved designs to database for invoice {invoice_record.id}")
                return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving designs to database: {str(e)}")
            return False
        
        return False
    
    def _safe_get(self, data: Dict[str, Any], key_path: str, default: Any = "") -> Any:
        """Safely get nested dictionary value using dot notation"""
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current if current is not None else default