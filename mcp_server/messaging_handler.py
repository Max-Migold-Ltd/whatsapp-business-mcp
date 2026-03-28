"""
Messaging handler for WhatsApp Cloud API - handles all types of messages.
"""

from typing import Dict, Any, List, Optional
from .base_handler import BaseWhatsAppHandler
from .models import (
    WhatsAppMessageRequest, MessageType, MediaObject, LocationObject, 
    ContactObject, InteractiveObject, ReactionObject, MessageContext,
    InteractiveType, InteractiveHeader, InteractiveBody, InteractiveFooter,
    InteractiveAction, ButtonAction, ListSection, ListRow
)

class MessagingHandler(BaseWhatsAppHandler):
    """Handler for all WhatsApp messaging operations"""
    
    async def send_text_message(
        self, 
        phone_number: str, 
        message: str, 
        preview_url: bool = False,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a text message"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": message,
                "preview_url": preview_url
            }
        }
        
        if context_message_id:
            payload["context"] = {"message_id": context_message_id}
        
        return await self._make_request("POST", self.messages_url, payload)
    
    async def send_media_message(
        self,
        phone_number: str,
        media_type: str,  # image, video, audio, document, sticker
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a media message (image, video, audio, document, sticker)"""
        if not media_id and not media_link:
            raise ValueError("Either media_id or media_link must be provided")
        
        media_object = {}
        if media_id:
            media_object["id"] = media_id
        else:
            media_object["link"] = media_link
            
        if caption and media_type in ["image", "video", "document"]:
            media_object["caption"] = caption
            
        if filename and media_type == "document":
            media_object["filename"] = filename
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual", 
            "to": phone_number,
            "type": media_type,
            media_type: media_object
        }
        
        if context_message_id:
            payload["context"] = {"message_id": context_message_id}
        
        return await self._make_request("POST", self.messages_url, payload)
    
    async def send_location_message(
        self,
        phone_number: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a location message"""
        location_object = {
            "latitude": latitude,
            "longitude": longitude
        }
        
        if name:
            location_object["name"] = name
        if address:
            location_object["address"] = address
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "location",
            "location": location_object
        }
        
        if context_message_id:
            payload["context"] = {"message_id": context_message_id}
        
        return await self._make_request("POST", self.messages_url, payload)
    
    async def send_contact_message(
        self,
        phone_number: str,
        contacts: List[Dict[str, Any]],
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a contact message"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "contacts",
            "contacts": contacts
        }
        
        if context_message_id:
            payload["context"] = {"message_id": context_message_id}
        
        return await self._make_request("POST", self.messages_url, payload)
    
    async def send_reaction_message(
        self,
        phone_number: str,
        message_id: str,
        emoji: str
    ) -> Dict[str, Any]:
        """Send a reaction to a message (use empty string to remove reaction)"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "reaction",
            "reaction": {
                "message_id": message_id,
                "emoji": emoji
            }
        }
        
        return await self._make_request("POST", self.messages_url, payload)
    
    async def send_button_message(
        self,
        phone_number: str,
        body_text: str,
        buttons: List[Dict[str, str]],  # [{"type": "reply", "title": "Button Title", "id": "button_id"}]
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an interactive button message"""
        
        # Convert simple button format to required format
        button_actions = []
        for i, button in enumerate(buttons[:3]):  # Max 3 buttons
            button_actions.append({
                "type": "reply",
                "reply": {
                    "id": button.get("id", f"button_{i}"),
                    "title": button["title"]
                }
            })
        
        interactive_object = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": button_actions}
        }
        
        if header_text:
            interactive_object["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive_object["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "interactive",
            "interactive": interactive_object
        }
        
        if context_message_id:
            payload["context"] = {"message_id": context_message_id}
        
        return await self._make_request("POST", self.messages_url, payload)
    
    async def send_list_message(
        self,
        phone_number: str,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],  # [{"title": "Section Title", "rows": [{"id": "row_id", "title": "Row Title", "description": "Optional description"}]}]
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an interactive list message"""
        
        interactive_object = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
        
        if header_text:
            interactive_object["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive_object["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "interactive",
            "interactive": interactive_object
        }
        
        if context_message_id:
            payload["context"] = {"message_id": context_message_id}
        
        return await self._make_request("POST", self.messages_url, payload)
    
    async def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read"""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        return await self._make_request("POST", self.messages_url, payload)
    
    # Helper methods for building complex message structures
    
    def build_contact_object(
        self,
        formatted_name: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        organization: Optional[str] = None
    ) -> Dict[str, Any]:
        """Helper to build contact object"""
        contact = {
            "name": {"formatted_name": formatted_name}
        }
        
        if first_name:
            contact["name"]["first_name"] = first_name
        if last_name:
            contact["name"]["last_name"] = last_name
            
        if phone_number:
            contact["phones"] = [{"phone": phone_number, "type": "CELL"}]
            
        if email:
            contact["emails"] = [{"email": email, "type": "WORK"}]
            
        if organization:
            contact["org"] = {"company": organization}
        
        return contact
    
    def build_list_section(
        self,
        title: str,
        rows: List[Dict[str, str]]  # [{"id": "row_id", "title": "Row Title", "description": "Optional desc"}]
    ) -> Dict[str, Any]:
        """Helper to build list section"""
        return {
            "title": title,
            "rows": rows
        }
    
    def build_button(
        self,
        title: str,
        button_id: Optional[str] = None,
        url: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Dict[str, str]:
        """Helper to build button object"""
        if url:
            return {"type": "url", "title": title, "url": url}
        elif phone_number:
            return {"type": "phone_number", "title": title, "phone_number": phone_number}
        else:
            return {"type": "reply", "title": title, "id": button_id or title.lower().replace(" ", "_")}