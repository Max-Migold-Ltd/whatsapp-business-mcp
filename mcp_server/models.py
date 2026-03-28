"""
Pydantic models for WhatsApp Cloud API based on the official Postman collection.
"""

from pydantic import BaseModel, validator, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum

# ================================
# ENUMS AND BASE TYPES
# ================================

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"
    REACTION = "reaction"

class InteractiveType(str, Enum):
    BUTTON = "button"
    LIST = "list"
    PRODUCT = "product"
    PRODUCT_LIST = "product_list"

class ComponentType(str, Enum):
    HEADER = "header"
    BODY = "body"
    FOOTER = "footer"
    BUTTON = "button"

class ButtonSubType(str, Enum):
    QUICK_REPLY = "quick_reply"
    URL = "url"
    PHONE_NUMBER = "phone_number"

class ParameterType(str, Enum):
    TEXT = "text"
    CURRENCY = "currency"
    DATE_TIME = "date_time"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    PAYLOAD = "payload"

class TemplateCategory(str, Enum):
    MARKETING = "MARKETING"
    UTILITY = "UTILITY"
    AUTHENTICATION = "AUTHENTICATION"

class RecipientType(str, Enum):
    INDIVIDUAL = "individual"

# ================================
# BASIC MESSAGE MODELS
# ================================

class WhatsAppMessage(BaseModel):
    """Basic text message model"""
    phone_number: str = Field(..., description="Recipient phone number with country code")
    message: str = Field(..., description="Text message content")
    
    @validator('phone_number', pre=True)
    def validate_phone_number(cls, v):
        import re
        cleaned = re.sub(r'[^\d+]', '', str(v))
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        if len(cleaned) < 10:
            raise ValueError("Phone number is too short")
        return cleaned

class MessageContext(BaseModel):
    """Context for reply messages"""
    message_id: str = Field(..., description="ID of the message being replied to")

# ================================
# MEDIA MODELS
# ================================

class MediaObject(BaseModel):
    """Media object for images, videos, documents, audio, stickers"""
    id: Optional[str] = None
    link: Optional[str] = None
    caption: Optional[str] = None
    filename: Optional[str] = None

class LocationObject(BaseModel):
    """Location object"""
    longitude: float = Field(..., description="Longitude coordinate")
    latitude: float = Field(..., description="Latitude coordinate")
    name: Optional[str] = None
    address: Optional[str] = None

# ================================
# CONTACT MODELS
# ================================

class ContactName(BaseModel):
    formatted_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    suffix: Optional[str] = None
    prefix: Optional[str] = None

class ContactPhone(BaseModel):
    phone: Optional[str] = None
    type: Optional[str] = None
    wa_id: Optional[str] = None

class ContactEmail(BaseModel):
    email: Optional[str] = None
    type: Optional[str] = None

class ContactAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    type: Optional[str] = None

class ContactOrg(BaseModel):
    company: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None

class ContactUrl(BaseModel):
    url: Optional[str] = None
    type: Optional[str] = None

class ContactObject(BaseModel):
    addresses: Optional[List[ContactAddress]] = None
    birthday: Optional[str] = None
    emails: Optional[List[ContactEmail]] = None
    name: ContactName
    org: Optional[ContactOrg] = None
    phones: Optional[List[ContactPhone]] = None
    urls: Optional[List[ContactUrl]] = None

# ================================
# INTERACTIVE MESSAGE MODELS
# ================================

class ButtonAction(BaseModel):
    type: str
    title: str
    id: Optional[str] = None
    url: Optional[str] = None
    phone_number: Optional[str] = None

class ListRow(BaseModel):
    id: str
    title: str
    description: Optional[str] = None

class ListSection(BaseModel):
    title: str
    rows: List[ListRow]

class InteractiveAction(BaseModel):
    button: Optional[str] = None  # For list messages
    buttons: Optional[List[ButtonAction]] = None  # For button messages
    sections: Optional[List[ListSection]] = None  # For list messages

class InteractiveHeader(BaseModel):
    type: str  # text, image, video, document
    text: Optional[str] = None
    image: Optional[MediaObject] = None
    video: Optional[MediaObject] = None
    document: Optional[MediaObject] = None

class InteractiveBody(BaseModel):
    text: str

class InteractiveFooter(BaseModel):
    text: str

class InteractiveObject(BaseModel):
    type: InteractiveType
    header: Optional[InteractiveHeader] = None
    body: InteractiveBody
    footer: Optional[InteractiveFooter] = None
    action: InteractiveAction

# ================================
# TEMPLATE MESSAGE MODELS
# ================================

class CurrencyObject(BaseModel):
    fallback_value: str
    code: str
    amount_1000: int

class DateTimeObject(BaseModel):
    fallback_value: str
    day_of_week: Optional[Union[str, int]] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day_of_month: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    calendar: Optional[str] = None

class TemplateParameter(BaseModel):
    type: ParameterType
    text: Optional[str] = None
    currency: Optional[CurrencyObject] = None
    date_time: Optional[DateTimeObject] = None
    image: Optional[MediaObject] = None
    document: Optional[MediaObject] = None
    video: Optional[MediaObject] = None
    payload: Optional[str] = None

class TemplateComponent(BaseModel):
    type: ComponentType
    parameters: Optional[List[TemplateParameter]] = None
    sub_type: Optional[ButtonSubType] = None
    index: Optional[int] = None

class LanguageObject(BaseModel):
    code: str
    policy: Optional[str] = "deterministic"

class TemplateObject(BaseModel):
    name: str
    language: LanguageObject
    components: Optional[List[TemplateComponent]] = None

# ================================
# REACTION MODEL
# ================================

class ReactionObject(BaseModel):
    message_id: str
    emoji: str  # Use empty string to remove reaction

# ================================
# COMPREHENSIVE MESSAGE MODEL
# ================================

class WhatsAppMessageRequest(BaseModel):
    """Comprehensive message request model supporting all message types"""
    messaging_product: str = "whatsapp"
    recipient_type: RecipientType = RecipientType.INDIVIDUAL
    to: str = Field(..., alias="phone_number")
    type: MessageType
    context: Optional[MessageContext] = None
    
    # Message content based on type
    text: Optional[Dict[str, Any]] = None
    image: Optional[MediaObject] = None
    audio: Optional[MediaObject] = None
    video: Optional[MediaObject] = None
    document: Optional[MediaObject] = None
    sticker: Optional[MediaObject] = None
    location: Optional[LocationObject] = None
    contacts: Optional[List[ContactObject]] = None
    interactive: Optional[InteractiveObject] = None
    template: Optional[TemplateObject] = None
    reaction: Optional[ReactionObject] = None

    model_config = {"populate_by_name": True}

# ================================
# TEMPLATE MANAGEMENT MODELS
# ================================

class TemplateHeaderComponent(BaseModel):
    type: str = "HEADER"
    format: str  # TEXT, IMAGE, VIDEO, DOCUMENT
    text: Optional[str] = None
    example: Optional[Dict[str, List[str]]] = None

class TemplateBodyComponent(BaseModel):
    type: str = "BODY"
    text: str
    example: Optional[Dict[str, List[List[str]]]] = None

class TemplateFooterComponent(BaseModel):
    type: str = "FOOTER"
    text: str

class TemplateButtonComponent(BaseModel):
    type: str = "BUTTONS"
    buttons: List[Dict[str, Any]]

class MessageTemplate(BaseModel):
    """Model for creating message templates"""
    name: str
    category: TemplateCategory
    language: str
    components: List[Union[TemplateHeaderComponent, TemplateBodyComponent, TemplateFooterComponent, TemplateButtonComponent]]

# ================================
# PHONE NUMBER MODELS
# ================================

class PhoneNumberInfo(BaseModel):
    verified_name: str
    display_phone_number: str
    id: str
    quality_rating: str

class PhoneNumberRegistration(BaseModel):
    messaging_product: str = "whatsapp"
    pin: str = Field(..., description="6-digit PIN for two-step verification")

class PhoneNumberVerification(BaseModel):
    code: str = Field(..., description="Verification code received via SMS")

# ================================
# BUSINESS PROFILE MODELS
# ================================

class BusinessProfile(BaseModel):
    about: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    profile_picture_url: Optional[str] = None
    websites: Optional[List[str]] = None
    vertical: Optional[str] = None

# ================================
# WEBHOOK MODELS
# ================================

class WebhookSubscription(BaseModel):
    object: str = "whatsapp_business_account"
    callback_url: str
    verify_token: str
    fields: List[str] = ["messages"]

# ================================
# RESPONSE MODELS
# ================================

class MessageResponse(BaseModel):
    messaging_product: str
    contacts: List[Dict[str, str]]
    messages: List[Dict[str, str]]

class ApiResponse(BaseModel):
    """Generic API response model"""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class TemplateResponse(BaseModel):
    """Response model for template operations"""
    data: Optional[List[Dict[str, Any]]] = None
    paging: Optional[Dict[str, Any]] = None

# ================================
# MEDIA UPLOAD MODELS
# ================================

class MediaUploadResponse(BaseModel):
    id: str

class MediaInfo(BaseModel):
    url: str
    mime_type: str
    sha256: str
    file_size: int
    id: str
    messaging_product: str

# ================================
# FLOW MODELS
# ================================

class FlowCategory(str, Enum):
    """Flow categories"""
    SIGN_UP = "SIGN_UP"
    SIGN_IN = "SIGN_IN"
    APPOINTMENT_BOOKING = "APPOINTMENT_BOOKING"
    CONTACT_US = "CONTACT_US"
    OTHER = "OTHER"

class FlowStatus(str, Enum):
    """Flow status"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"

class FlowPreview(BaseModel):
    """Flow preview model"""
    preview_url: str
    expires_at: str

class FlowValidationError(BaseModel):
    """Flow validation error model"""
    code: str
    message: str
    field: Optional[str] = None

class FlowObject(BaseModel):
    """Flow object model"""
    id: str
    name: str
    categories: List[FlowCategory]
    status: FlowStatus
    validation_errors: List[FlowValidationError] = []
    json_version: Optional[str] = None
    data_api_version: Optional[str] = None
    data_channel_uri: Optional[str] = None
    health_status: Optional[str] = None
    preview: Optional[FlowPreview] = None

# ================================
# ANALYTICS MODELS
# ================================

class AnalyticsGranularity(str, Enum):
    """Analytics granularity"""
    DAY = "DAY"
    HOUR = "HOUR"
    MONTH = "MONTH"
    MONTHLY = "MONTHLY"

class AnalyticsDataPoint(BaseModel):
    """Analytics data point model"""
    start: int
    end: int
    sent: Optional[int] = None
    delivered: Optional[int] = None
    read: Optional[int] = None
    failed: Optional[int] = None

class ConversationDirection(str, Enum):
    """Conversation direction"""
    BUSINESS_INITIATED = "business_initiated"
    USER_INITIATED = "user_initiated"

class ConversationType(str, Enum):
    """Conversation type"""
    FREE_ENTRY_POINT = "free_entry_point"
    FREE_TIER = "free_tier"
    REGULAR = "regular"

class AnalyticsResponse(BaseModel):
    """Analytics response model"""
    phone_numbers: List[str] = []
    country_codes: List[str] = []
    granularity: AnalyticsGranularity
    data_points: List[AnalyticsDataPoint]

# ================================
# BUSINESS ACCOUNT MODELS
# ================================

class AccountReviewStatus(str, Enum):
    """Account review status"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class AccountType(str, Enum):
    """Account type"""
    BUSINESS = "BUSINESS"
    ENTERPRISE = "ENTERPRISE"

class WABAObject(BaseModel):
    """WABA object model"""
    id: str
    name: str
    currency: str
    timezone_id: str
    message_template_namespace: Optional[str] = None
    account_review_status: AccountReviewStatus
    account_type: AccountType
    owner_business_info: Optional[Dict[str, Any]] = None
    owner_business: Optional[Dict[str, Any]] = None
    primary_funding_id: Optional[str] = None
    owner: Optional[Dict[str, Any]] = None