"""
Base handler class for WhatsApp Cloud API operations.
"""

import os
import re
import httpx
from typing import Dict, Any, Optional
from .models import ApiResponse

class BaseWhatsAppHandler:
    """Base class for all WhatsApp API handlers"""

    # Patterns that may contain sensitive data in error messages
    _SENSITIVE_PATTERNS = [
        re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]+', re.IGNORECASE),
        re.compile(r'access_token=[A-Za-z0-9_\-\.]+', re.IGNORECASE),
        re.compile(r'EAA[A-Za-z0-9]+'),  # Meta access token format
        re.compile(r'https?://[^\s]+'),  # URLs that may contain tokens as query params
    ]

    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("META_PHONE_NUMBER_ID")
        self.business_account_id = os.getenv("META_BUSINESS_ACCOUNT_ID")
        self.waba_id = os.getenv("WABA_ID")
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v22.0")

        # Validate required environment variables
        if not self.access_token:
            raise ValueError("META_ACCESS_TOKEN environment variable is required")
        if not self.phone_number_id:
            raise ValueError("META_PHONE_NUMBER_ID environment variable is required")

        # Base URLs for different types of operations
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.messages_url = f"{self.base_url}/{self.phone_number_id}/messages"
        self.media_url = f"{self.base_url}/{self.phone_number_id}/media"

        # Templates and WABA operations use WABA_ID (fallback to business_account_id if not set)
        waba_for_operations = self.waba_id or self.business_account_id
        if waba_for_operations:
            self.templates_url = f"{self.base_url}/{waba_for_operations}/message_templates"
            self.phone_numbers_url = f"{self.base_url}/{waba_for_operations}/phone_numbers"
            self.subscriptions_url = f"{self.base_url}/{waba_for_operations}/subscribed_apps"
            self.waba_info_url = f"{self.base_url}/{waba_for_operations}"

        # Business profile operations use META_BUSINESS_ACCOUNT_ID
        if self.business_account_id:
            self.business_profile_url = f"{self.base_url}/{self.business_account_id}"

    def _sanitize_error(self, error) -> str:
        """Strip tokens, URLs, and other sensitive data from error messages."""
        message = str(error)
        for pattern in self._SENSITIVE_PATTERNS:
            message = pattern.sub("[REDACTED]", message)
        return message
        
    def _prepare_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Prepare standard headers for API requests"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "MCP-WhatsApp-Server/1.0"
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to WhatsApp API"""
        try:
            headers = self._prepare_headers() if not files else self._prepare_headers(content_type=None)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    if files:
                        response = await client.post(url, headers=headers, files=files, data=data)
                    else:
                        response = await client.post(url, headers=headers, json=data, params=params)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle different response status codes
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        return {
                            "status": "success",
                            "data": response_data,
                            "status_code": response.status_code
                        }
                    except ValueError:
                        # Response is not JSON
                        return {
                            "status": "success",
                            "data": {"text": response.text},
                            "status_code": response.status_code
                        }
                else:
                    # Handle error responses
                    try:
                        error_data = response.json()
                        return {
                            "status": "error",
                            "error": error_data,
                            "status_code": response.status_code,
                            "message": f"API request failed with status {response.status_code}"
                        }
                    except ValueError:
                        return {
                            "status": "error",
                            "error": {"text": response.text},
                            "status_code": response.status_code,
                            "message": f"API request failed with status {response.status_code}"
                        }
                        
        except httpx.TimeoutException:
            return {
                "status": "error",
                "error": {"type": "timeout", "message": "Request timed out"},
                "message": "Request to WhatsApp API timed out"
            }
        except httpx.RequestError as e:
            return {
                "status": "error",
                "error": {"type": "request_error", "message": type(e).__name__},
                "message": f"Request failed: {type(e).__name__}"
            }
        except Exception:
            return {
                "status": "error",
                "error": {"type": "unexpected_error", "message": "An unexpected error occurred"},
                "message": "An unexpected error occurred"
            }
    
    def _validate_required_vars(self, required_vars: list) -> None:
        """Validate that required environment variables are set"""
        missing_vars = []
        for var in required_vars:
            if not getattr(self, var.lower().replace("meta_", "").replace("_", "_"), None):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def _build_url(self, endpoint: str, **kwargs) -> str:
        """Build URL with dynamic parameters"""
        url = f"{self.base_url}/{endpoint}"
        for key, value in kwargs.items():
            url = url.replace(f"{{{key}}}", str(value))
        return url