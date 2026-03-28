"""
Template handler for WhatsApp Cloud API - handles message template operations.
"""

from typing import Dict, Any, List, Optional
from .base_handler import BaseWhatsAppHandler
from .models import (
    TemplateObject, TemplateComponent, TemplateParameter, LanguageObject,
    MessageTemplate, TemplateCategory, ComponentType, ParameterType,
    CurrencyObject, DateTimeObject, MediaObject
)

class TemplateHandler(BaseWhatsAppHandler):
    """Handler for WhatsApp message template operations"""
    
    def __init__(self):
        super().__init__()
        # Validate WABA ID is available for template operations
        if not (self.waba_id or self.business_account_id):
            raise ValueError("Either WABA_ID or META_BUSINESS_ACCOUNT_ID environment variable is required for template operations")
    
    # ================================
    # TEMPLATE MANAGEMENT OPERATIONS
    # ================================
    
    async def get_message_templates(
        self,
        name: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get message templates with optional filtering"""
        params = {"limit": limit}
        
        if name:
            params["name"] = name
        if status:
            params["status"] = status
        if category:
            params["category"] = category
        if language:
            params["language"] = language
        
        return await self._make_request("GET", self.templates_url, params=params)
    
    async def get_template_by_name(self, template_name: str) -> Dict[str, Any]:
        """Get a specific template by name"""
        return await self.get_message_templates(name=template_name)
    
    async def create_message_template(
        self,
        name: str,
        category: str,
        language: str,
        components: List[Dict[str, Any]],
        allow_category_change: bool = False
    ) -> Dict[str, Any]:
        """Create a new message template"""
        payload = {
            "name": name,
            "category": category.upper(),
            "language": language,
            "components": components
        }
        
        if allow_category_change:
            payload["allow_category_change"] = True
        
        return await self._make_request("POST", self.templates_url, payload)
    
    async def delete_message_template(
        self,
        template_name: str,
        hsm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a message template"""
        params = {"name": template_name}
        if hsm_id:
            params["hsm_id"] = hsm_id
        
        return await self._make_request("DELETE", self.templates_url, params=params)
    
    # ================================
    # TEMPLATE MESSAGE SENDING
    # ================================
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a template message"""
        template_object = {
            "name": template_name,
            "language": {"code": language_code}
        }
        
        if components:
            template_object["components"] = components
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "template",
            "template": template_object
        }
        
        if context_message_id:
            payload["context"] = {"message_id": context_message_id}
        
        return await self._make_request("POST", self.messages_url, payload)
    
    async def send_template_with_text_parameters(
        self,
        phone_number: str,
        template_name: str,
        language_code: str = "en_US",
        header_parameters: Optional[List[str]] = None,
        body_parameters: Optional[List[str]] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send template message with text parameters"""
        components = []
        
        if header_parameters:
            components.append({
                "type": "header",
                "parameters": [{"type": "text", "text": param} for param in header_parameters]
            })
        
        if body_parameters:
            components.append({
                "type": "body", 
                "parameters": [{"type": "text", "text": param} for param in body_parameters]
            })
        
        return await self.send_template_message(
            phone_number, template_name, language_code, components, context_message_id
        )
    
    async def send_template_with_media_header(
        self,
        phone_number: str,
        template_name: str,
        language_code: str,
        media_type: str,  # image, video, document
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        body_parameters: Optional[List[str]] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send template message with media in header"""
        if not media_id and not media_link:
            raise ValueError("Either media_id or media_link must be provided")
        
        # Build media parameter
        media_param = {"type": media_type}
        if media_id:
            media_param[media_type] = {"id": media_id}
        else:
            media_param[media_type] = {"link": media_link}
        
        components = [{
            "type": "header",
            "parameters": [media_param]
        }]
        
        if body_parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in body_parameters]
            })
        
        return await self.send_template_message(
            phone_number, template_name, language_code, components, context_message_id
        )
    
    async def send_template_with_buttons(
        self,
        phone_number: str,
        template_name: str,
        language_code: str,
        button_parameters: List[Dict[str, Any]],  # [{"index": 0, "type": "payload", "payload": "value"}]
        body_parameters: Optional[List[str]] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send template message with button parameters"""
        components = []
        
        if body_parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in body_parameters]
            })
        
        # Add button components
        for button_param in button_parameters:
            components.append({
                "type": "button",
                "sub_type": "quick_reply",
                "index": button_param["index"],
                "parameters": [{
                    "type": button_param["type"],
                    button_param["type"]: button_param.get("payload", button_param.get("text", ""))
                }]
            })
        
        return await self.send_template_message(
            phone_number, template_name, language_code, components, context_message_id
        )
    
    async def send_template_with_currency(
        self,
        phone_number: str,
        template_name: str,
        language_code: str,
        currency_code: str,
        amount_1000: int,  # Amount multiplied by 1000
        fallback_value: str,
        body_parameters: Optional[List[str]] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send template message with currency parameter"""
        currency_param = {
            "type": "currency",
            "currency": {
                "fallback_value": fallback_value,
                "code": currency_code,
                "amount_1000": amount_1000
            }
        }
        
        components = [{
            "type": "body",
            "parameters": [currency_param] + ([{"type": "text", "text": param} for param in (body_parameters or [])])
        }]
        
        return await self.send_template_message(
            phone_number, template_name, language_code, components, context_message_id
        )
    
    async def send_template_with_datetime(
        self,
        phone_number: str,
        template_name: str,
        language_code: str,
        fallback_value: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day_of_month: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        day_of_week: Optional[int] = None,
        calendar: str = "GREGORIAN",
        body_parameters: Optional[List[str]] = None,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send template message with date_time parameter"""
        datetime_obj = {"fallback_value": fallback_value}
        
        if year:
            datetime_obj["year"] = year
        if month:
            datetime_obj["month"] = month
        if day_of_month:
            datetime_obj["day_of_month"] = day_of_month
        if hour:
            datetime_obj["hour"] = hour
        if minute:
            datetime_obj["minute"] = minute
        if day_of_week:
            datetime_obj["day_of_week"] = day_of_week
        if calendar:
            datetime_obj["calendar"] = calendar
        
        datetime_param = {
            "type": "date_time",
            "date_time": datetime_obj
        }
        
        components = [{
            "type": "body",
            "parameters": [datetime_param] + ([{"type": "text", "text": param} for param in (body_parameters or [])])
        }]
        
        return await self.send_template_message(
            phone_number, template_name, language_code, components, context_message_id
        )
    
    # ================================
    # TEMPLATE BUILDING HELPERS
    # ================================
    
    def build_text_template_component(
        self,
        component_type: str,  # HEADER, BODY, FOOTER
        text: str,
        example_values: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Build a text template component"""
        component = {
            "type": component_type,
            "text": text
        }
        
        if component_type == "HEADER":
            component["format"] = "TEXT"
            
        if example_values and "{{" in text:
            if component_type == "BODY":
                component["example"] = {"body_text": [example_values]}
            else:
                component["example"] = {"header_text": example_values}
        
        return component
    
    def build_media_template_component(
        self,
        media_type: str,  # IMAGE, VIDEO, DOCUMENT
        example_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build a media template component for header"""
        component = {
            "type": "HEADER",
            "format": media_type.upper()
        }
        
        if example_url:
            component["example"] = {"header_handle": [example_url]}
        
        return component
    
    def build_button_template_component(
        self,
        buttons: List[Dict[str, str]]  # [{"type": "QUICK_REPLY", "text": "Button Text"}]
    ) -> Dict[str, Any]:
        """Build a buttons template component"""
        button_objects = []
        
        for button in buttons:
            button_obj = {
                "type": button["type"],
                "text": button["text"]
            }
            
            if button["type"] == "URL":
                button_obj["url"] = button.get("url", "https://example.com")
            elif button["type"] == "PHONE_NUMBER":
                button_obj["phone_number"] = button.get("phone_number", "+1234567890")
                
            button_objects.append(button_obj)
        
        return {
            "type": "BUTTONS",
            "buttons": button_objects
        }
    
    def build_complete_template(
        self,
        name: str,
        category: str,
        language: str,
        header_text: Optional[str] = None,
        body_text: str = "",
        footer_text: Optional[str] = None,
        buttons: Optional[List[Dict[str, str]]] = None,
        header_media_type: Optional[str] = None,
        example_values: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Build a complete template for creation"""
        components = []
        
        # Header component
        if header_text:
            components.append(self.build_text_template_component(
                "HEADER", header_text, 
                example_values.get("header") if example_values else None
            ))
        elif header_media_type:
            components.append(self.build_media_template_component(header_media_type))
        
        # Body component (required)
        if body_text:
            components.append(self.build_text_template_component(
                "BODY", body_text,
                example_values.get("body") if example_values else None
            ))
        
        # Footer component
        if footer_text:
            components.append(self.build_text_template_component("FOOTER", footer_text))
        
        # Buttons component
        if buttons:
            components.append(self.build_button_template_component(buttons))
        
        return {
            "name": name,
            "category": category.upper(),
            "language": language,
            "components": components
        }