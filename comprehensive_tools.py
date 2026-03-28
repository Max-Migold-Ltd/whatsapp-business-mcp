"""
Comprehensive WhatsApp Cloud API tools for MCP Server.
This file contains all the tool definitions to keep main.py manageable.
"""

from typing import List, Dict, Any, Optional

def register_comprehensive_tools(mcp, messaging_handler, template_handler, business_handler, media_handler):
    """Register all comprehensive WhatsApp Cloud API tools with the MCP server"""
    
    # ================================
    # TEXT MESSAGING TOOLS
    # ================================

    @mcp.tool()
    async def send_text_message(
        phone_number: str, 
        message: str, 
        preview_url: bool = False,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send a text message with advanced options.
        
        Args:
            phone_number: Recipient phone number with country code
            message: Text message content
            preview_url: Whether to show URL previews
            reply_to_message_id: ID of message to reply to (optional)
            
        Returns:
            dict: Response with message status and ID
        """
        try:
            return await messaging_handler.send_text_message(
                phone_number, message, preview_url, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def send_reaction(phone_number: str, message_id: str, emoji: str) -> dict:
        """
        React to a message with an emoji.
        
        Args:
            phone_number: Recipient phone number
            message_id: ID of the message to react to
            emoji: Emoji to use for reaction (use empty string to remove)
            
        Returns:
            dict: Response with reaction status
        """
        try:
            return await messaging_handler.send_reaction_message(phone_number, message_id, emoji)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ================================
    # TEMPLATE MANAGEMENT TOOLS
    # ================================

    @mcp.tool()
    async def get_message_templates(
        name: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 100
    ) -> dict:
        """
        Get message templates with optional filtering.
        
        Args:
            name: Filter by template name
            status: Filter by template status (APPROVED, PENDING, REJECTED)
            category: Filter by category (MARKETING, UTILITY, AUTHENTICATION)
            language: Filter by language code
            limit: Maximum number of templates to return
            
        Returns:
            dict: List of message templates
        """
        try:
            return await template_handler.get_message_templates(name, status, category, language, limit)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def send_template_message(
        phone_number: str,
        template_name: str,
        language_code: str = "en_US",
        body_parameters: Optional[List[str]] = None,
        header_parameters: Optional[List[str]] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send a template message with text parameters.
        
        Args:
            phone_number: Recipient phone number
            template_name: Name of the approved template
            language_code: Language code (e.g., en_US, pt_BR)
            body_parameters: List of parameters for template body variables
            header_parameters: List of parameters for template header variables
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            return await template_handler.send_template_with_text_parameters(
                phone_number, template_name, language_code, header_parameters, body_parameters, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def create_message_template(
        name: str,
        category: str,
        language: str,
        body_text: str,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> dict:
        """
        Create a new message template.
        
        Args:
            name: Template name (lowercase, underscore-separated)
            category: Template category (MARKETING, UTILITY, AUTHENTICATION)
            language: Language code (e.g., en_US, pt_BR)
            body_text: Main template text (can include {{1}}, {{2}} for variables)
            header_text: Optional header text
            footer_text: Optional footer text
            buttons: Optional buttons [{"type": "QUICK_REPLY", "text": "Button Text"}]
            
        Returns:
            dict: Template creation response
        """
        try:
            template_data = template_handler.build_complete_template(
                name, category, language, header_text, body_text, footer_text, buttons
            )
            return await template_handler.create_message_template(
                template_data["name"],
                template_data["category"],
                template_data["language"],
                template_data["components"]
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def delete_message_template(template_name: str) -> dict:
        """
        Delete a message template.
        
        Args:
            template_name: Name of the template to delete
            
        Returns:
            dict: Deletion response
        """
        try:
            return await template_handler.delete_message_template(template_name)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def send_template_with_media_header(
        phone_number: str,
        template_name: str,
        language_code: str,
        media_type: str,
        media_url: Optional[str] = None,
        media_id: Optional[str] = None,
        body_parameters: Optional[List[str]] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send a template message with media in the header.
        
        Args:
            phone_number: Recipient phone number
            template_name: Name of the approved template
            language_code: Language code
            media_type: Type of media (image, video, document)
            media_url: URL of the media file
            media_id: ID of uploaded media
            body_parameters: List of parameters for template body
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            return await template_handler.send_template_with_media_header(
                phone_number, template_name, language_code, media_type, media_id, media_url, body_parameters, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ================================
    # MEDIA MESSAGING TOOLS
    # ================================

    @mcp.tool()
    async def send_image_message(
        phone_number: str,
        image_url: Optional[str] = None,
        image_id: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send an image message.
        
        Args:
            phone_number: Recipient phone number
            image_url: URL of the image (if not using uploaded media)
            image_id: ID of uploaded image media
            caption: Optional image caption
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            return await messaging_handler.send_media_message(
                phone_number, "image", image_id, image_url, caption, None, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def send_video_message(
        phone_number: str,
        video_url: Optional[str] = None,
        video_id: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send a video message.
        
        Args:
            phone_number: Recipient phone number
            video_url: URL of the video
            video_id: ID of uploaded video media
            caption: Optional video caption
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            return await messaging_handler.send_media_message(
                phone_number, "video", video_id, video_url, caption, None, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def send_document_message(
        phone_number: str,
        document_url: Optional[str] = None,
        document_id: Optional[str] = None,
        filename: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send a document message.
        
        Args:
            phone_number: Recipient phone number
            document_url: URL of the document
            document_id: ID of uploaded document media
            filename: Document filename
            caption: Optional document caption
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            return await messaging_handler.send_media_message(
                phone_number, "document", document_id, document_url, caption, filename, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ================================
    # INTERACTIVE MESSAGING TOOLS
    # ================================

    @mcp.tool()
    async def send_button_message(
        phone_number: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send an interactive button message.
        
        Args:
            phone_number: Recipient phone number
            body_text: Main message text
            buttons: List of buttons [{"title": "Button Text", "id": "button_id"}]
            header_text: Optional header text
            footer_text: Optional footer text
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            return await messaging_handler.send_button_message(
                phone_number, body_text, buttons, header_text, footer_text, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def send_list_message(
        phone_number: str,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send an interactive list message.
        
        Args:
            phone_number: Recipient phone number
            body_text: Main message text
            button_text: Text for the list button
            sections: List sections [{"title": "Section", "rows": [{"id": "row_id", "title": "Row Title"}]}]
            header_text: Optional header text
            footer_text: Optional footer text
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            return await messaging_handler.send_list_message(
                phone_number, body_text, button_text, sections, header_text, footer_text, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ================================
    # LOCATION AND CONTACT TOOLS
    # ================================

    @mcp.tool()
    async def send_location_message(
        phone_number: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send a location message.
        
        Args:
            phone_number: Recipient phone number
            latitude: Location latitude
            longitude: Location longitude
            name: Location name
            address: Location address
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            return await messaging_handler.send_location_message(
                phone_number, latitude, longitude, name, address, reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def send_contact_message(
        phone_number: str,
        contact_name: str,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ) -> dict:
        """
        Send a contact message.
        
        Args:
            phone_number: Recipient phone number
            contact_name: Name of the contact to send
            contact_phone: Phone number of the contact
            contact_email: Email of the contact
            reply_to_message_id: ID of message to reply to
            
        Returns:
            dict: Response with message status
        """
        try:
            contact = messaging_handler.build_contact_object(
                contact_name, None, None, contact_phone, contact_email
            )
            return await messaging_handler.send_contact_message(
                phone_number, [contact], reply_to_message_id
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ================================
    # MEDIA MANAGEMENT TOOLS
    # ================================

    @mcp.tool()
    async def upload_media(file_path: str, media_type: str = "auto") -> dict:
        """
        Upload a media file and get media ID.
        
        Args:
            file_path: Path to the file to upload
            media_type: Type of media (auto, image, video, audio, document)
            
        Returns:
            dict: Response with media ID
        """
        try:
            return await media_handler.upload_media(file_path, media_type)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def get_media_info(media_id: str) -> dict:
        """
        Get information about uploaded media.
        
        Args:
            media_id: ID of the uploaded media
            
        Returns:
            dict: Media information including download URL
        """
        try:
            return await media_handler.get_media_info(media_id)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ================================
    # BUSINESS MANAGEMENT TOOLS
    # ================================

    @mcp.tool()
    async def get_business_profile() -> dict:
        """
        Get the business profile information.
        
        Returns:
            dict: Business profile data
        """
        try:
            return await business_handler.get_business_profile()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    async def get_phone_numbers() -> dict:
        """
        Get all phone numbers associated with the business account.
        
        Returns:
            dict: List of phone numbers with their information
        """
        try:
            return await business_handler.get_phone_numbers()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ================================
    # UTILITY TOOLS  
    # ================================

    @mcp.tool()
    async def mark_message_as_read(message_id: str) -> dict:
        """
        Mark a received message as read.
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            dict: Response with read status
        """
        try:
            return await messaging_handler.mark_message_as_read(message_id)
        except Exception as e:
            return {"status": "error", "message": str(e)}