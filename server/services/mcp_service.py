"""
MCP Service - Handles communication with Model Context Protocol servers

This service provides a clean abstraction layer for interacting with MCP servers,
specifically the Google Drive MCP server for contract file operations.
"""
import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import base64

logger = logging.getLogger(__name__)


class OAuthExpiredError(Exception):
    """Custom exception for OAuth token expiration"""
    pass


class MCPService:
    """Service for interacting with MCP (Model Context Protocol) servers"""
    
    def __init__(self):
        self.gdrive_mcp_path = self._get_gdrive_mcp_path()
        # Add cache for search results to prevent duplicate calls
        self._search_cache = {}
        self._cache_ttl = 60  # Cache for 60 seconds
    
    def _get_gdrive_mcp_path(self) -> str:
        """Get the path to the Google Drive MCP server"""
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        mcp_path = os.path.join(
            base_path, "mcp", "gdrive_mcp", "gdrive-mcp-server", "dist", "index.js"
        )
        return mcp_path
    
    def _get_cache_key(self, method: str, *args) -> str:
        """Generate cache key for method and arguments"""
        return f"{method}:{':'.join(str(arg) for arg in args if arg is not None)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if cache_key not in self._search_cache:
            return False
        
        cached_time, _ = self._search_cache[cache_key]
        return (time.time() - cached_time) < self._cache_ttl
    
    def _get_cached_result(self, cache_key: str):
        """Get cached result if valid"""
        if self._is_cache_valid(cache_key):
            _, result = self._search_cache[cache_key]
            return result
        return None
    
    def _cache_result(self, cache_key: str, result):
        """Cache the result with current timestamp"""
        self._search_cache[cache_key] = (time.time(), result)
    
    def _execute_mcp_command(self, request: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Execute a command against the MCP server"""
        if not os.path.exists(self.gdrive_mcp_path):
            raise FileNotFoundError(f"MCP server not found at: {self.gdrive_mcp_path}")
        
        command = ["node", self.gdrive_mcp_path]
        
        # Set the correct working directory for the MCP server
        # The MCP server should run from the parent directory of dist/
        mcp_working_dir = os.path.dirname(os.path.dirname(self.gdrive_mcp_path))
        
        # Set up environment variables for the MCP server
        env = os.environ.copy()
        credentials_path = os.path.join(mcp_working_dir, "credentials", ".gdrive-server-credentials.json")
        env["MCP_GDRIVE_CREDENTIALS"] = credentials_path
        
        logger.debug(f"MCP working directory: {mcp_working_dir}")
        logger.debug(f"MCP credentials path: {credentials_path}")
        logger.debug(f"Credentials file exists: {os.path.exists(credentials_path)}")
        
        try:
            # Prepare input data
            input_data = json.dumps(request)
            logger.debug(f"MCP request: {input_data}")
            
            # Use shell command approach as it works better with MCP server
            shell_cmd = f"echo '{input_data}' | node dist/index.js"
            
            process = subprocess.run(
                shell_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=mcp_working_dir,  # Run from MCP server directory
                env=env  # Pass environment variables
            )
            
            if process.returncode != 0:
                logger.error(f"MCP command failed: {process.stderr}")
                raise RuntimeError(f"MCP command failed: {process.stderr}")
            
            response = json.loads(process.stdout)
            
            if "error" in response:
                error_msg = response['error'].get('message', '').lower()
                # Check for OAuth-related errors
                if "invalid_request" in error_msg or "unauthorized" in error_msg or "token" in error_msg:
                    # Create a special OAuth error that can be caught by the route handler
                    raise OAuthExpiredError("Google Drive authentication has expired. Please re-authenticate.")
                raise RuntimeError(f"MCP error: {response['error']['message']}")
            
            return response
        
        except subprocess.TimeoutExpired:
            logger.error("MCP command timed out")
            raise TimeoutError("MCP command timed out")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MCP response: {e}")
            logger.error(f"Raw stdout: '{process.stdout}'")
            logger.error(f"Raw stderr: '{process.stderr}'")
            logger.error(f"Return code: {process.returncode}")
            raise RuntimeError("Failed to parse MCP server response")
    
    def search_files(self, query: str) -> List[Dict[str, str]]:
        """
        Search for files in Google Drive using MCP
        
        Args:
            query: Search query string
            
        Returns:
            List of file information dictionaries
        """
        logger.info(f"🔍 Searching Google Drive for files: {query}")
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "gdrive_search",
                "arguments": {
                    "query": query
                }
            }
        }
        
        response = self._execute_mcp_command(request)
        
        # Extract file information from MCP response
        content = response.get("result", {}).get("content", [])
        if not content:
            return []
        
        # Parse the file list from MCP response text
        file_text = content[0].get("text", "")
        files_found = []
        
        # Extract file information from response text
        lines = file_text.split('\n')[1:]  # Skip the "Found X files:" line
        for line in lines:
            if line.strip() and " - ID: " in line:
                # Parse format: "filename (mimetype) - ID: file_id"
                parts = line.rsplit(" - ID: ", 1)
                if len(parts) == 2:
                    name_mime = parts[0].strip()
                    file_id = parts[1].strip()
                    
                    # Extract name and mime type
                    if " (" in name_mime and name_mime.endswith(")"):
                        name = name_mime.split(" (")[0]
                        mime_type = name_mime.split(" (")[1][:-1]
                    else:
                        name = name_mime
                        mime_type = "unknown"
                    
                    files_found.append({
                        "file_id": file_id,
                        "name": name,
                        "mime_type": mime_type,
                        "gdrive_uri": f"gdrive:///{file_id}"
                    })
        
        logger.info(f"✅ Found {len(files_found)} files")
        return files_found
    
    def read_file_content(self, file_id: str) -> Tuple[str, str]:
        """
        Read file content from Google Drive using MCP
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Tuple of (content, mime_type)
        """
        logger.info(f"📖 Reading file content: {file_id}")
        
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "gdrive_read_file",
                "arguments": {
                    "file_id": file_id
                }
            }
        }
        
        response = self._execute_mcp_command(request, timeout=60)
        
        content_data = response.get("result", {}).get("content", [])
        if not content_data:
            raise ValueError(f"No content found for file: {file_id}")
        
        file_content = content_data[0].get("text", "")
        
        logger.info(f"✅ Successfully read file content")
        return file_content, "unknown"
    
    def download_file_to_temp(self, file_id: str, filename: str) -> str:
        """
        Download file content to a temporary file
        
        Args:
            file_id: Google Drive file ID
            filename: Original filename (for extension detection)
            
        Returns:
            Path to temporary file
        """
        content, mime_type = self.read_file_content(file_id)
        
        # Determine file extension
        suffix = Path(filename).suffix or ".txt"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            # Handle different content types
            if mime_type == "application/pdf" or suffix.lower() == ".pdf":
                # Content should be base64 for PDFs
                try:
                    file_bytes = base64.b64decode(content)
                    tmp_file.write(file_bytes)
                except Exception as e:
                    logger.warning(f"Failed to decode base64 content, treating as text: {e}")
                    tmp_file.write(content.encode())
            else:
                # Text content
                tmp_file.write(content.encode())
            
            tmp_file_path = tmp_file.name
        
        logger.info(f"📁 Downloaded file to temporary path: {tmp_file_path}")
        return tmp_file_path
    
    def search_contracts(self, query: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Search specifically for contract files in Google Drive
        
        Args:
            query: Optional custom search query
            
        Returns:
            List of contract file information
        """
        if query is None:
            query = "contract or rental agreement"
        
        # Check cache first
        cache_key = self._get_cache_key("search_contracts", query)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            logger.info(f"🚀 Using cached search results for contracts query: {query}")
            return cached_result
        
        files = self.search_files(query)
        
        # Filter for likely contract files
        contract_extensions = {'.pdf'}
        contract_keywords = {
            'contract', 'agreement', 'conditions', 'service', 'consulting',
            'rental', 'lease', 'rent', 'tenancy', 'landlord', 'tenant', 'property'
        }
        
        contracts = []
        for file_info in files:
            filename = file_info['name'].lower()
            extension = Path(filename).suffix.lower()
            
            # Check if it's likely a contract based on name or extension
            is_contract = (
                extension in contract_extensions or
                any(keyword in filename for keyword in contract_keywords)
            )
            
            if is_contract:
                contracts.append(file_info)
        
        logger.info(f"🔍 Filtered to {len(contracts)} likely contract files")
        
        # Cache the result
        self._cache_result(cache_key, contracts)
        
        return contracts
    
    def search_rental_contracts(self, query: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Search specifically for rental contract files in Google Drive
        
        Args:
            query: Optional custom search query for rental contracts
            
        Returns:
            List of rental contract file information
        """
        if query is None:
            query = "rental"
        
        # Check cache first
        cache_key = self._get_cache_key("search_rental_contracts", query)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            logger.info(f"🚀 Using cached search results for rental contracts query: {query}")
            return cached_result
        
        files = self.search_files(query)
        
        # Filter for rental-specific files
        rental_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        rental_keywords = {
            'rental', 'lease', 'rent', 'tenancy', 'landlord', 'tenant', 'property',
            'apartment', 'house', 'commercial', 'residential', 'premises'
        }
        
        rental_contracts = []
        for file_info in files:
            filename = file_info['name'].lower()
            extension = Path(filename).suffix.lower()
            
            # Check if it's likely a rental contract based on name or extension
            is_rental_contract = (
                extension in rental_extensions and
                any(keyword in filename for keyword in rental_keywords)
            )
            
            if is_rental_contract:
                rental_contracts.append(file_info)
        
        logger.info(f"🏠 Filtered to {len(rental_contracts)} likely rental contract files")
        
        # Cache the result
        self._cache_result(cache_key, rental_contracts)
        
        return rental_contracts


# Global singleton instance
_mcp_service_instance = None

def get_mcp_service() -> MCPService:
    """Get singleton MCP service instance"""
    global _mcp_service_instance
    if _mcp_service_instance is None:
        _mcp_service_instance = MCPService()
    return _mcp_service_instance