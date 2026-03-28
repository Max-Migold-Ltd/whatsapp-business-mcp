import os
import httpx
from typing import Dict, Any
from pydantic import BaseModel, validator
import re

class WhatsAppMessage(BaseModel):
    phone_number: str
    message: str

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Strip whitespace then validate format: + followed by digits only
        cleaned = v.strip()
        if not cleaned.startswith('+'):
            cleaned = '+' + re.sub(r'[^\d]', '', cleaned)
        # Must be + followed by digits only
        if not re.match(r'^\+\d+$', cleaned):
            raise ValueError("Phone number must start with + followed by digits only")
        if len(cleaned) < 10:
            raise ValueError("Phone number is too short")
        if len(cleaned) > 20:
            raise ValueError("Phone number is too long (max 20 characters)")
        return cleaned

    @validator('message')
    def validate_message_length(cls, v):
        if len(v) > 4096:
            raise ValueError("Message exceeds WhatsApp maximum length of 4096 characters")
        return v

class WhatsAppHandler:
    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("META_PHONE_NUMBER_ID")
        self.api_version = "v22.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        
        if not self.access_token or not self.phone_number_id:
            raise ValueError("Missing required environment variables. Please set META_ACCESS_TOKEN and META_PHONE_NUMBER_ID")

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for the API request."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _prepare_payload(self, message_data: WhatsAppMessage) -> Dict[str, Any]:
        """Prepare the payload for the API request."""
        return {
            "messaging_product": "whatsapp",
            "to": message_data.phone_number,
            "type": "text",
            "text": {
                "body": message_data.message
            }
        }

    async def send_message(self, message_data: WhatsAppMessage) -> Dict[str, Any]:
        """
        Send a WhatsApp message using the Meta API.
        
        Args:
            message_data: WhatsAppMessage object containing phone_number and message
            
        Returns:
            Dict containing the API response
            
        Raises:
            Exception: If the API request fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self._prepare_headers(),
                    json=self._prepare_payload(message_data)
                )
                response.raise_for_status()
                
                return {
                    "status": "success",
                    "message": "Message sent successfully",
                    "response": response.json()
                }
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            raise Exception(error_msg)
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def validate_message(self, message_data: WhatsAppMessage) -> bool:
        """
        Validate the message data.
        
        Args:
            message_data: WhatsAppMessage object to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # A validação do phone_number já é feita pelo validator do Pydantic
            if not message_data.message or len(message_data.message.strip()) == 0:
                return False
            return True
        except Exception:
            return False 