from typing import List, Dict, Any, Optional
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import re
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invoice-templates", tags=["invoice-templates"])

class DiscoveredTemplate(BaseModel):
    id: str
    fileName: str
    filePath: str
    componentName: str
    templateName: str
    fileSize: int
    lastModified: str
    templateType: str
    modelUsed: str
    generatedBy: str

class TemplateListResponse(BaseModel):
    templates: List[DiscoveredTemplate]
    total: int

@router.get("/", response_model=TemplateListResponse)
async def list_invoice_templates():
    """Scan and return all discovered invoice template files"""
    try:
        templates = await scan_invoice_templates()
        return TemplateListResponse(
            templates=templates,
            total=len(templates)
        )
    except Exception as e:
        logger.error(f"Error listing invoice templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list invoice templates")

@router.get("/{template_id}/content")
async def get_template_content(template_id: str):
    """Get the content of a specific template file"""
    try:
        templates = await scan_invoice_templates()
        template = next((t for t in templates if t.id == template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Read file content
        with open(template.filePath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "template": template,
            "content": content
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template file not found")
    except Exception as e:
        logger.error(f"Error reading template content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read template content")

async def scan_invoice_templates() -> List[DiscoveredTemplate]:
    """Scan the client/src/components/invoices directory for invoice template files"""
    try:
        # Path to the client invoices components directory
        invoices_dir = Path(__file__).parent.parent.parent / "client" / "src" / "components" / "invoices"
        
        if not invoices_dir.exists():
            logger.warning(f"Invoices directory not found: {invoices_dir}")
            return []
        
        templates = []
        
        # Get all .tsx files that contain 'invoice' in the name
        tsx_files = [f for f in invoices_dir.iterdir() 
                    if f.is_file() and f.suffix == '.tsx' and 'invoice' in f.name.lower()]
        
        for file_path in tsx_files:
            try:
                # Get file stats
                stat = file_path.stat()
                
                # Read file content to extract metadata
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata
                metadata = extract_metadata_from_content(content)
                component_name = extract_component_name(file_path.name, content)
                
                template = DiscoveredTemplate(
                    id=generate_id_from_filename(file_path.name),
                    fileName=file_path.name,
                    filePath=str(file_path),
                    componentName=component_name,
                    templateName=file_path.stem,
                    fileSize=stat.st_size,
                    lastModified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    templateType=metadata.get('templateType', 'Invoice Template'),
                    modelUsed=metadata.get('modelUsed', 'gemini-2.0-flash'),
                    generatedBy=metadata.get('generatedBy', 'ui_invoice_generator')
                )
                
                templates.append(template)
                
            except Exception as e:
                logger.error(f"Error processing template file {file_path}: {str(e)}")
                continue
        
        # Sort by last modified date (newest first)
        templates.sort(key=lambda x: x.lastModified, reverse=True)
        
        return templates
        
    except Exception as e:
        logger.error(f"Error scanning invoice templates: {str(e)}")
        return []

def extract_component_name(filename: str, content: str) -> str:
    """Extract component name from filename and content"""
    
    # First try to extract from export default
    export_match = re.search(r'export default (?:function\s+)?(\w+)', content)
    if export_match:
        return export_match.group(1)
    
    # Try to extract from function declaration
    function_match = re.search(r'(?:function|const)\s+(\w+)', content)
    if function_match:
        return function_match.group(1)
    
    # Fallback to filename-based extraction
    if 'invoice-component-' in filename:
        return 'InvoiceComponent'
    elif 'invoice-' in filename:
        return 'Invoice'
    
    # Generic fallback
    base_name = filename.replace('.tsx', '').replace('-', ' ').title().replace(' ', '')
    return base_name

def extract_metadata_from_content(content: str) -> Dict[str, str]:
    """Extract metadata from file content"""
    metadata = {}
    
    # Look for comment-based metadata
    patterns = {
        'generatedBy': r'//.*Generated by:?\s*(.+)',
        'modelUsed': r'//.*Model:?\s*(.+)',
        'templateType': r'//.*Type:?\s*(.+)',
        'description': r'//.*Description:?\s*(.+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            metadata[key] = match.group(1).strip()
    
    # Infer template type from content
    if 'InvoiceData' in content or 'interface Invoice' in content:
        metadata.setdefault('templateType', 'Professional Invoice Template')
    
    # Infer model from content
    if 'gemini' in content.lower():
        metadata.setdefault('modelUsed', 'gemini-2.0-flash')
    
    # Set defaults
    metadata.setdefault('generatedBy', 'ui_invoice_generator')
    metadata.setdefault('templateType', 'Invoice Template')
    metadata.setdefault('modelUsed', 'AI Generated')
    
    return metadata

def generate_id_from_filename(filename: str) -> str:
    """Generate unique ID from filename"""
    return filename.replace('.tsx', '').replace('/', '-').replace('\\', '-')