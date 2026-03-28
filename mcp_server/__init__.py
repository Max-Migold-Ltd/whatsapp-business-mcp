"""
MCP Server package for comprehensive WhatsApp Cloud API operations.
"""

# Legacy imports for backward compatibility
from .whatsapp_handler import WhatsAppHandler, WhatsAppMessage

# New comprehensive handlers
from .base_handler import BaseWhatsAppHandler
from .messaging_handler import MessagingHandler
from .template_handler import TemplateHandler
from .business_handler import BusinessHandler
from .media_handler import MediaHandler
from .flow_handler import FlowHandler
from .analytics_handler import AnalyticsHandler
from .webhook_handler import WebhookHandler
from .business_account_handler import BusinessAccountHandler

# Models
from .models import (
    WhatsAppMessageRequest, MessageType, InteractiveType,
    TemplateObject, TemplateComponent, TemplateParameter,
    MediaObject, LocationObject, ContactObject, InteractiveObject,
    MessageTemplate, TemplateCategory, BusinessProfile,
    ApiResponse, MessageResponse
)

__all__ = [
    # Legacy
    'WhatsAppHandler', 'WhatsAppMessage',
    
    # Handlers
    'BaseWhatsAppHandler', 'MessagingHandler', 'TemplateHandler', 
    'BusinessHandler', 'MediaHandler', 'FlowHandler', 'AnalyticsHandler',
    'WebhookHandler', 'BusinessAccountHandler',
    
    # Models
    'WhatsAppMessageRequest', 'MessageType', 'InteractiveType',
    'TemplateObject', 'TemplateComponent', 'TemplateParameter',
    'MediaObject', 'LocationObject', 'ContactObject', 'InteractiveObject',
    'MessageTemplate', 'TemplateCategory', 'BusinessProfile',
    'ApiResponse', 'MessageResponse', 'FlowObject', 'FlowCategory', 'FlowStatus',
    'AnalyticsResponse', 'AnalyticsGranularity', 'WABAObject', 'AccountReviewStatus',
    'AccountType', 'WebhookSubscription'
] 