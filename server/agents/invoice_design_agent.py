from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime, date
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
            
            # Generate actual HTML invoices with embedded data
            html_invoices = await self.generate_html_invoices(designs, invoice_data)
            
            # Store designs and HTML invoices in database and state
            await self._save_designs_to_database(state, designs, html_invoices)
            
            # Store designs and HTML invoices in state
            state["invoice_designs"] = designs
            state["html_invoices"] = html_invoices
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

Here is the invoice data: {json.dumps(contract_data, indent=2, default=self._json_serializer)}

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
    
    async def generate_html_invoices(self, designs: Dict[str, Any], invoice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate complete HTML invoices with embedded data from the design specifications
        
        Args:
            designs: The UI design specifications
            invoice_data: The actual invoice data to embed
            
        Returns:
            List of HTML invoice strings with embedded data
        """
        try:
            html_invoices = []
            
            # Extract actual data from invoice_data
            actual_data = self._extract_actual_invoice_data(invoice_data)
            
            for design in designs.get("designs", []):
                try:
                    # Generate HTML for this design
                    html_content = await self._generate_html_from_design(design, actual_data)
                    
                    html_invoices.append({
                        "design_name": design.get("design_name", "Unknown Design"),
                        "design_id": design.get("design_id", "unknown"),
                        "html_content": html_content,
                        "generated_at": datetime.now().isoformat()
                    })
                    
                    self.logger.info(f"✅ Generated HTML invoice for design: {design.get('design_name')}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to generate HTML for design {design.get('design_name')}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Generated {len(html_invoices)} HTML invoices")
            return html_invoices
            
        except Exception as e:
            self.logger.error(f"❌ Error generating HTML invoices: {str(e)}")
            return []

    async def _generate_html_from_design(self, design: Dict[str, Any], actual_data: Dict[str, Any]) -> str:
        """Generate complete HTML from design specification with actual data"""
        
        design_name = design.get("design_name", "Invoice")
        components = design.get("components", [])
        
        # Create HTML structure
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{design_name} - {actual_data.get('invoice_number', 'Invoice')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .invoice-container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .invoice-title {{
            font-size: 36px;
            color: #333;
            margin: 0;
        }}
        .invoice-number {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        .parties-section {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }}
        .party {{
            flex: 1;
        }}
        .party h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 16px;
        }}
        .party p {{
            margin: 5px 0;
            color: #666;
            font-size: 14px;
        }}
        .line-items {{
            margin: 30px 0;
        }}
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .items-table th,
        .items-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .items-table th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }}
        .summary {{
            text-align: right;
            margin-top: 30px;
        }}
        .summary-row {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 8px 0;
        }}
        .summary-total {{
            font-weight: bold;
            font-size: 18px;
            border-top: 2px solid #333;
            padding-top: 10px;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="invoice-container">
        <div class="header">
            <h1 class="invoice-title">INVOICE</h1>
            <div class="invoice-number">Invoice #: {actual_data.get('invoice_number', 'N/A')}</div>
            <div class="invoice-number">Date: {actual_data.get('invoice_date', 'N/A')}</div>
            <div class="invoice-number">Due Date: {actual_data.get('due_date', 'N/A')}</div>
        </div>
        
        <div class="parties-section">
            <div class="party">
                <h3>Bill To:</h3>
                <p><strong>{actual_data.get('client_name', 'Client Name')}</strong></p>
                <p>{actual_data.get('client_address', 'Client Address')}</p>
                {f"<p>{actual_data.get('client_email', '')}</p>" if actual_data.get('client_email') else ""}
                {f"<p>{actual_data.get('client_phone', '')}</p>" if actual_data.get('client_phone') else ""}
            </div>
            <div class="party">
                <h3>From:</h3>
                <p><strong>{actual_data.get('service_provider_name', 'Service Provider')}</strong></p>
                <p>{actual_data.get('service_provider_address', 'Provider Address')}</p>
                {f"<p>{actual_data.get('service_provider_email', '')}</p>" if actual_data.get('service_provider_email') else ""}
                {f"<p>{actual_data.get('service_provider_phone', '')}</p>" if actual_data.get('service_provider_phone') else ""}
            </div>
        </div>
        
        <div class="line-items">
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Quantity</th>
                        <th>Rate</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{actual_data.get('contract_title', 'Service')}</td>
                        <td>1</td>
                        <td>{actual_data.get('currency', 'USD')} {actual_data.get('subtotal', '0.00')}</td>
                        <td>{actual_data.get('currency', 'USD')} {actual_data.get('total_amount', '0.00')}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="summary">
            <div class="summary-row">
                <span>Subtotal:</span>
                <span>{actual_data.get('currency', 'USD')} {actual_data.get('subtotal', '0.00')}</span>
            </div>
            <div class="summary-row">
                <span>Tax:</span>
                <span>{actual_data.get('currency', 'USD')} {actual_data.get('tax_amount', '0.00')}</span>
            </div>
            <div class="summary-row summary-total">
                <span>Total:</span>
                <span>{actual_data.get('currency', 'USD')} {actual_data.get('total_amount', '0.00')}</span>
            </div>
        </div>
        
        <div class="footer">
            <p>Thank you for your business!</p>
        </div>
    </div>
</body>
</html>"""
        
        return html_content

    def _extract_actual_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actual invoice data from the nested structure for HTML generation"""
        
        actual_data = {}
        
        try:
            # Handle nested invoice data structure
            if "invoice_header" in invoice_data:
                header = invoice_data["invoice_header"]
                actual_data.update({
                    "invoice_number": header.get("invoice_number"),
                    "invoice_date": header.get("invoice_date"),
                    "due_date": header.get("due_date")
                })
            
            if "parties" in invoice_data:
                parties = invoice_data["parties"]
                if "client" in parties:
                    client = parties["client"]
                    actual_data.update({
                        "client_name": client.get("name"),
                        "client_email": client.get("email"),
                        "client_address": client.get("address"),
                        "client_phone": client.get("phone")
                    })
                
                if "service_provider" in parties:
                    provider = parties["service_provider"]
                    actual_data.update({
                        "service_provider_name": provider.get("name"),
                        "service_provider_email": provider.get("email"),
                        "service_provider_address": provider.get("address"),
                        "service_provider_phone": provider.get("phone")
                    })
            
            if "financial_details" in invoice_data:
                financial = invoice_data["financial_details"]
                actual_data.update({
                    "subtotal": financial.get("subtotal"),
                    "tax_amount": financial.get("tax_amount"),
                    "total_amount": financial.get("total_amount"),
                    "currency": financial.get("currency")
                })
            
            if "contract_details" in invoice_data:
                contract = invoice_data["contract_details"]
                actual_data.update({
                    "contract_title": contract.get("contract_title")
                })
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting invoice data: {str(e)}")
        
        return actual_data

    async def _save_designs_to_database(self, state: WorkflowState, designs: Dict[str, Any], html_invoices: List[Dict[str, Any]] = None) -> bool:
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
                
                # Also save HTML invoices if provided
                if html_invoices:
                    updated_invoice_data['html_invoices'] = html_invoices
                
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

    def _json_serializer(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")