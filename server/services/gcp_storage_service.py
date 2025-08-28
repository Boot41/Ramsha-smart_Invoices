from google.cloud import storage
from typing import Optional, BinaryIO, Dict, Any, List
import os
import logging
from datetime import datetime, timedelta
import mimetypes
from io import BytesIO

logger = logging.getLogger(__name__)


class GCPStorageService:
    """Google Cloud Storage service for file operations"""
    
    def __init__(self):
        self.project_id = os.getenv("PROJECT_ID")
        self.bucket_name = os.getenv("GCP_STORAGE_BUCKET", f"{self.project_id}-documents")
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not self.project_id:
            raise ValueError("PROJECT_ID must be set in environment variables")
        
        try:
            # Initialize Google Cloud Storage client
            self.client = storage.Client(project=self.project_id)
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Create bucket if it doesn't exist
            self._ensure_bucket_exists()
            
            logger.info(f"✅ GCP Storage Service initialized for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GCP Storage Service: {str(e)}")
            raise
    
    def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists"""
        try:
            # Check if bucket exists
            self.bucket.reload()
            logger.info(f"✅ Bucket '{self.bucket_name}' exists")
        except Exception:
            try:
                # Create bucket if it doesn't exist
                self.bucket = self.client.create_bucket(self.bucket_name)
                logger.info(f"✅ Created bucket '{self.bucket_name}'")
            except Exception as e:
                logger.error(f"❌ Failed to create bucket '{self.bucket_name}': {str(e)}")
                raise
    
    def upload_file(
        self, 
        file_content: bytes, 
        destination_path: str, 
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to GCP Storage
        
        Args:
            file_content: File content as bytes
            destination_path: Path in bucket where file will be stored
            content_type: MIME type of the file
            metadata: Additional metadata to store with file
            
        Returns:
            Dictionary with upload results
        """
        try:
            logger.info(f"🚀 Uploading file to GCP Storage: {destination_path}")
            
            # Create blob object
            blob = self.bucket.blob(destination_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            else:
                # Try to guess content type from filename
                blob.content_type = mimetypes.guess_type(destination_path)[0] or 'application/octet-stream'
            
            # Set metadata
            if metadata:
                blob.metadata = metadata
            
            # Upload file
            blob.upload_from_string(file_content, content_type=blob.content_type)
            
            # Generate download URL (valid for 1 hour)
            download_url = self.generate_download_url(destination_path, expires_in_hours=1)
            
            result = {
                "success": True,
                "message": "✅ File uploaded successfully",
                "bucket_name": self.bucket_name,
                "file_path": destination_path,
                "file_size": len(file_content),
                "content_type": blob.content_type,
                "download_url": download_url,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            logger.info(f"✅ File uploaded successfully: {destination_path} ({len(file_content)} bytes)")
            return result
            
        except Exception as e:
            error_msg = f"❌ Failed to upload file {destination_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e),
                "file_path": destination_path
            }
    
    def download_file(self, source_path: str) -> Optional[bytes]:
        """
        Download file from GCP Storage
        
        Args:
            source_path: Path of file in bucket
            
        Returns:
            File content as bytes, or None if not found
        """
        try:
            logger.info(f"📥 Downloading file from GCP Storage: {source_path}")
            
            blob = self.bucket.blob(source_path)
            
            if not blob.exists():
                logger.warning(f"⚠️ File not found: {source_path}")
                return None
            
            content = blob.download_as_bytes()
            logger.info(f"✅ File downloaded successfully: {source_path} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"❌ Failed to download file {source_path}: {str(e)}")
            return None
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete file from GCP Storage
        
        Args:
            file_path: Path of file in bucket
            
        Returns:
            Dictionary with deletion results
        """
        try:
            logger.info(f"🗑️ Deleting file from GCP Storage: {file_path}")
            
            blob = self.bucket.blob(file_path)
            
            if not blob.exists():
                return {
                    "success": False,
                    "message": f"File not found: {file_path}",
                    "file_path": file_path
                }
            
            blob.delete()
            
            logger.info(f"✅ File deleted successfully: {file_path}")
            return {
                "success": True,
                "message": f"✅ File deleted successfully: {file_path}",
                "file_path": file_path,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = f"❌ Failed to delete file {file_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e),
                "file_path": file_path
            }
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in GCP Storage
        
        Args:
            file_path: Path of file in bucket
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            blob = self.bucket.blob(file_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"❌ Error checking file existence {file_path}: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from GCP Storage
        
        Args:
            file_path: Path of file in bucket
            
        Returns:
            Dictionary with file information or None if not found
        """
        try:
            blob = self.bucket.blob(file_path)
            
            if not blob.exists():
                return None
            
            blob.reload()
            
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "md5_hash": blob.md5_hash,
                "crc32c": blob.crc32c,
                "metadata": blob.metadata or {}
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get file info {file_path}: {str(e)}")
            return None
    
    def generate_download_url(self, file_path: str, expires_in_hours: int = 1) -> Optional[str]:
        """
        Generate signed URL for file download
        
        Args:
            file_path: Path of file in bucket
            expires_in_hours: URL expiration time in hours
            
        Returns:
            Signed URL or None if failed
        """
        try:
            blob = self.bucket.blob(file_path)
            
            # Generate signed URL that expires in specified hours
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expires_in_hours),
                method="GET"
            )
            
            logger.info(f"✅ Generated download URL for {file_path} (expires in {expires_in_hours}h)")
            return url
            
        except Exception as e:
            logger.error(f"❌ Failed to generate download URL for {file_path}: {str(e)}")
            return None
    
    def list_files(self, prefix: str = "", max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List files in bucket with optional prefix filter
        
        Args:
            prefix: Prefix to filter files
            max_results: Maximum number of files to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            logger.info(f"📋 Listing files with prefix: {prefix}")
            
            blobs = self.bucket.list_blobs(prefix=prefix, max_results=max_results)
            files = []
            
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "created": blob.time_created.isoformat() if blob.time_created else None,
                    "updated": blob.updated.isoformat() if blob.updated else None
                })
            
            logger.info(f"✅ Found {len(files)} files with prefix '{prefix}'")
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to list files with prefix {prefix}: {str(e)}")
            return []
    
    def upload_from_stream(
        self, 
        file_stream: BinaryIO, 
        destination_path: str, 
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file from stream to GCP Storage
        
        Args:
            file_stream: File stream (like uploaded file)
            destination_path: Path in bucket where file will be stored
            content_type: MIME type of the file
            metadata: Additional metadata to store with file
            
        Returns:
            Dictionary with upload results
        """
        try:
            # Read content from stream
            file_content = file_stream.read()
            file_stream.seek(0)  # Reset stream position
            
            return self.upload_file(file_content, destination_path, content_type, metadata)
            
        except Exception as e:
            error_msg = f"❌ Failed to upload from stream to {destination_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e),
                "file_path": destination_path
            }


# Global service instance
_gcp_storage_service = None

def get_gcp_storage_service() -> GCPStorageService:
    """Get singleton GCP Storage service instance"""
    global _gcp_storage_service
    if _gcp_storage_service is None:
        _gcp_storage_service = GCPStorageService()
    return _gcp_storage_service