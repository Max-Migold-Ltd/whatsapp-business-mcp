"""
Media handler for WhatsApp Cloud API - handles media upload and management.
"""

import os
from typing import Dict, Any, Optional, BinaryIO
from .base_handler import BaseWhatsAppHandler

class MediaHandler(BaseWhatsAppHandler):
    """Handler for WhatsApp media operations"""
    
    # ================================
    # MEDIA UPLOAD OPERATIONS
    # ================================
    
    async def upload_media(
        self,
        file_path: str,
        media_type: str = "auto"  # auto, image, video, audio, document
    ) -> Dict[str, Any]:
        """Upload media file and get media ID"""
        # Path traversal protection: resolve real path and check it stays within allowed directory
        allowed_dir = os.getenv("MEDIA_UPLOAD_DIR", "/tmp/whatsapp-media/")
        real_path = os.path.realpath(file_path)
        real_allowed = os.path.realpath(allowed_dir)

        if not real_path.startswith(real_allowed + os.sep) and real_path != real_allowed:
            return {
                "status": "error",
                "message": f"Access denied: file must be within the allowed upload directory ({allowed_dir})"
            }

        if not os.path.exists(real_path):
            return {
                "status": "error",
                "message": "File not found"
            }

        # Determine media type if auto
        if media_type == "auto":
            media_type = self._detect_media_type(real_path)

        # Use context manager for safe file handling
        with open(real_path, "rb") as f:
            files = {
                "file": ("media", f, self._get_mime_type(real_path)),
                "messaging_product": (None, "whatsapp"),
                "type": (None, media_type)
            }
            result = await self._make_request("POST", self.media_url, files=files)

        return result
    
    async def upload_media_from_bytes(
        self,
        file_data: bytes,
        filename: str,
        media_type: str = "auto"
    ) -> Dict[str, Any]:
        """Upload media from bytes data"""
        if media_type == "auto":
            media_type = self._detect_media_type_from_filename(filename)
        
        files = {
            "file": (filename, file_data, self._get_mime_type_from_filename(filename)),
            "messaging_product": (None, "whatsapp"),
            "type": (None, media_type)
        }
        
        return await self._make_request("POST", self.media_url, files=files)
    
    async def get_media_info(self, media_id: str) -> Dict[str, Any]:
        """Get media information by ID"""
        url = f"{self.base_url}/{media_id}"
        return await self._make_request("GET", url)
    
    async def download_media(self, media_id: str) -> Dict[str, Any]:
        """Get media download URL"""
        # First get media info to get the download URL
        media_info = await self.get_media_info(media_id)
        
        if media_info["status"] == "success" and "data" in media_info:
            download_url = media_info["data"].get("url")
            if download_url:
                # Get the actual media content
                return await self._make_request("GET", download_url)
        
        return media_info
    
    async def delete_media(self, media_id: str) -> Dict[str, Any]:
        """Delete uploaded media"""
        url = f"{self.base_url}/{media_id}"
        return await self._make_request("DELETE", url)
    
    # ================================
    # HELPER METHODS
    # ================================
    
    def _detect_media_type(self, file_path: str) -> str:
        """Detect media type from file extension"""
        extension = os.path.splitext(file_path)[1].lower()
        
        image_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        video_extensions = [".mp4", ".3gp", ".mov", ".avi"]
        audio_extensions = [".aac", ".amr", ".mp3", ".m4a", ".ogg", ".opus"]
        document_extensions = [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt"]
        
        if extension in image_extensions:
            return "image"
        elif extension in video_extensions:
            return "video"
        elif extension in audio_extensions:
            return "audio"
        elif extension in document_extensions:
            return "document"
        else:
            return "document"  # Default to document for unknown types
    
    def _detect_media_type_from_filename(self, filename: str) -> str:
        """Detect media type from filename"""
        return self._detect_media_type(filename)
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type from file extension"""
        extension = os.path.splitext(file_path)[1].lower()
        return self._get_mime_type_from_extension(extension)
    
    def _get_mime_type_from_filename(self, filename: str) -> str:
        """Get MIME type from filename"""
        extension = os.path.splitext(filename)[1].lower()
        return self._get_mime_type_from_extension(extension)
    
    def _get_mime_type_from_extension(self, extension: str) -> str:
        """Get MIME type from file extension"""
        mime_types = {
            # Images
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", 
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
            
            # Videos
            ".mp4": "video/mp4",
            ".3gp": "video/3gpp",
            ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
            ".mkv": "video/x-matroska",
            
            # Audio
            ".aac": "audio/aac",
            ".amr": "audio/amr",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".opus": "audio/opus",
            ".wav": "audio/wav",
            
            # Documents
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".zip": "application/zip",
            ".rar": "application/x-rar-compressed"
        }
        
        return mime_types.get(extension, "application/octet-stream")
    
    # ================================
    # MEDIA VALIDATION
    # ================================
    
    def validate_media_requirements(self, file_path: str, media_type: str) -> Dict[str, Any]:
        """Validate media file meets WhatsApp requirements"""
        if not os.path.exists(file_path):
            return {"valid": False, "error": "File not found"}
        
        file_size = os.path.getsize(file_path)
        extension = os.path.splitext(file_path)[1].lower()
        
        # WhatsApp media size limits
        size_limits = {
            "image": 5 * 1024 * 1024,      # 5MB
            "video": 16 * 1024 * 1024,     # 16MB
            "audio": 16 * 1024 * 1024,     # 16MB
            "document": 100 * 1024 * 1024,  # 100MB
            "sticker": 500 * 1024           # 500KB
        }
        
        # Supported formats
        supported_formats = {
            "image": [".jpg", ".jpeg", ".png", ".webp"],
            "video": [".mp4", ".3gp"],
            "audio": [".aac", ".amr", ".mp3", ".m4a", ".ogg", ".opus"],
            "document": [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt"],
            "sticker": [".webp"]
        }
        
        # Check file size
        if file_size > size_limits.get(media_type, 100 * 1024 * 1024):
            return {
                "valid": False,
                "error": f"File size ({file_size} bytes) exceeds limit for {media_type} ({size_limits.get(media_type)} bytes)"
            }
        
        # Check format
        if extension not in supported_formats.get(media_type, []):
            return {
                "valid": False,
                "error": f"File format {extension} not supported for {media_type}. Supported: {supported_formats.get(media_type, [])}"
            }
        
        return {"valid": True, "message": "Media file meets requirements"}
    
    # ================================
    # CONVENIENCE METHODS
    # ================================
    
    async def upload_image(self, file_path: str) -> Dict[str, Any]:
        """Upload an image file"""
        validation = self.validate_media_requirements(file_path, "image")
        if not validation["valid"]:
            return {"status": "error", "message": validation["error"]}
        
        return await self.upload_media(file_path, "image")
    
    async def upload_video(self, file_path: str) -> Dict[str, Any]:
        """Upload a video file"""
        validation = self.validate_media_requirements(file_path, "video")
        if not validation["valid"]:
            return {"status": "error", "message": validation["error"]}
        
        return await self.upload_media(file_path, "video")
    
    async def upload_audio(self, file_path: str) -> Dict[str, Any]:
        """Upload an audio file"""
        validation = self.validate_media_requirements(file_path, "audio")
        if not validation["valid"]:
            return {"status": "error", "message": validation["error"]}
        
        return await self.upload_media(file_path, "audio")
    
    async def upload_document(self, file_path: str) -> Dict[str, Any]:
        """Upload a document file"""
        validation = self.validate_media_requirements(file_path, "document")
        if not validation["valid"]:
            return {"status": "error", "message": validation["error"]}
        
        return await self.upload_media(file_path, "document")