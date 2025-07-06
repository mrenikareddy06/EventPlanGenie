# coordinator/state_schema.py
"""
State Schema Definitions for EventPlanGenie
Defines the comprehensive TypedDict structures for state management
"""

from typing import Dict, List, Any, Optional, TypedDict, Literal, Union
from datetime import datetime
from enum import Enum
from langchain_core.messages import BaseMessage

class EventType(Enum):
    """Supported event types"""
    BIRTHDAY_PARTY = "birthday_party"
    WEDDING = "wedding"
    CORPORATE_EVENT = "corporate_event"
    ANNIVERSARY = "anniversary"
    GRADUATION = "graduation"
    BABY_SHOWER = "baby_shower"
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    NETWORKING = "networking"
    CELEBRATION = "celebration"
    CUSTOM = "custom"

class EventStatus(Enum):
    """Event planning status"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AgentType(Enum):
    """Available agent types"""
    IDEA = "idea"
    LOCATION = "location"
    VENDOR_RESEARCH = "vendor_research"
    SCHEDULER = "scheduler"
    INVITATION = "invitation"
    REVIEWER = "reviewer"
    EMAIL = "email"

class PriorityLevel(Enum):
    """Priority levels for tasks and requirements"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Base type definitions
class ContactInfo(TypedDict):
    """Contact information structure"""
    name: str
    email: Optional[str]
    phone: Optional[str]
    role: Optional[str]

class Address(TypedDict):
    """Address structure"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    coordinates: Optional[Dict[str, float]]

class EventIdea(TypedDict):
    """Event idea structure"""
    id: str
    title: str
    description: str
    theme: str
    estimated_cost: float
    duration_hours: int
    suitable_venues: List[str]
    required_services: List[str]
    pros: List[str]
    cons: List[str]
    creativity_score: float
    feasibility_score: float

class LocationSuggestion(TypedDict):
    """Location suggestion structure"""
    id: str
    name: str
    type: str  # venue, restaurant, outdoor, etc.
    address: Address
    capacity: int
    cost_per_hour: Optional[float]
    amenities: List[str]
    availability: Dict[str, bool]
    contact_info: ContactInfo
    rating: Optional[float]
    reviews: List[str]
    photos: List[str]
    booking_requirements: Dict[str, Any]

class VendorService(TypedDict):
    """Vendor service structure"""
    id: str
    name: str
    category: str  # catering, photography, music, etc.
    description: str
    contact_info: ContactInfo
    services_offered: List[str]
    pricing: Dict[str, float]
    availability: Dict[str, bool]
    portfolio: List[str]
    rating: Optional[float]
    reviews: List[str]
    certifications: List[str]
    booking_requirements: Dict[str, Any]

class ScheduleItem(TypedDict):
    """Schedule item structure"""
    id: str
    title: str
    description: str
    start_time: str
    end_time: str
    duration_minutes: int
    location: str
    responsible_person: str
    required_vendors: List[str]
    priority: PriorityLevel
    notes: str
    dependencies: List[str]

class InvitationDetails(TypedDict):
    """Invitation details structure"""
    title: str
    subtitle: str
    event_description: str
    date_time: str
    location: str
    dress_code: Optional[str]
    rsvp_details: Dict[str, Any]
    special_instructions: str
    contact_info: ContactInfo
    design_theme: str
    color_scheme: List[str]

class ReviewFeedback(TypedDict):
    """Review feedback structure"""
    id: str
    reviewer: str
    timestamp: str
    category: str
    rating: int
    comments: str
    suggestions: List[str]
    approval_status: str
    priority: PriorityLevel

class ExportSettings(TypedDict):
    """Export settings structure"""
    formats: List[str]  # pdf, markdown, ics, etc.
    include_images: bool
    include_contact_info: bool
    include_schedule: bool
    include_vendor_details: bool
    custom_branding: Dict[str, Any]

class EmailSettings(TypedDict):
    """Email settings structure"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    from_name: str
    use_tls: bool
    template_style: str

# Main state schema
class EventPlanState(TypedDict):
    """
    Comprehensive state schema for the entire event planning workflow
    This is the central Context in the MCP (Model-Context-Protocol) architecture
    """
    
    # === CORE WORKFLOW MANAGEMENT ===
    messages: List[BaseMessage]
    current_stage: str
    workflow_history: List[Dict[str, Any]]
    user_inputs: Dict[str, Any]
    agent_outputs: Dict[str, Any]
    errors: List[Dict[str, Any]]
    progress_percentage: int
    
    # === EVENT CORE INFORMATION ===
    event_id: Optional[str]
    event_type: Optional[str]
    event_status: Optional[str]
    event_theme: Optional[str]
    event_title: Optional[str]
    event_description: Optional[str]
    
    # === BUDGET & LOGISTICS ===
    budget: Optional[float]
    budget_breakdown: Optional[Dict[str, float]]
    estimated_guests: Optional[int]
    confirmed_guests: Optional[int]
    preferred_date: Optional[str]
    preferred_time: Optional[str]
    duration_hours: Optional[int]
    
    # === LOCATION & VENUE ===
    location_preferences: Dict[str, Any]
    suggested_locations: List[LocationSuggestion]
    selected_location: Optional[LocationSuggestion]
    venue_requirements: Dict[str, Any]
    venue_booking_status: Optional[str]
    
    # === VENDOR & SERVICES ===
    vendor_categories: List[str]
    vendor_research_results: Dict[str, List[VendorService]]
    selected_vendors: Dict[str, VendorService]
    service_requirements: Dict[str, Any]
    vendor_booking_status: Dict[str, str]
    
    # === SCHEDULE & TIMELINE ===
    event_schedule: Optional[Dict[str, Any]]
    timeline_breakdown: List[ScheduleItem]
    schedule_approved: bool
    schedule_revisions: List[Dict[str, Any]]
    critical_deadlines: List[Dict[str, Any]]
    
    # === INVITATION & COMMUNICATION ===
    invitation_content: Optional[InvitationDetails]
    invitation_style: Optional[str]
    guest_list: List[ContactInfo]
    rsvp_details: Dict[str, Any]
    communication_history: List[Dict[str, Any]]
    
    # === REVIEW & QUALITY CONTROL ===
    review_feedback: List[ReviewFeedback]
    revision_requests: List[Dict[str, Any]]
    quality_score: Optional[float]
    approval_status: Optional[str]
    stakeholder_approvals: Dict[str, bool]
    
    # === EXPORT & DISTRIBUTION ===
    export_formats: List[str]
    export_settings: Optional[ExportSettings]
    generated_files: Dict[str, str]
    email_settings: Optional[EmailSettings]
    distribution_status: Dict[str, Any]
    
    # === USER PREFERENCES & CONTEXT ===
    user_preferences: Dict[str, Any]
    user_profile: Optional[Dict[str, Any]]
    conversation_context: List[Dict[str, Any]]
    agent_memories: Dict[str, Any]
    previous_events: List[Dict[str, Any]]
    
    # === STREAMING & UI ===
    streaming_enabled: bool
    ui_updates: List[Dict[str, Any]]
    real_time_status: Optional[str]
    
    # === ADVANCED FEATURES ===
    weather_data: Optional[Dict[str, Any]]
    traffic_considerations: Optional[Dict[str, Any]]
    accessibility_requirements: Dict[str, Any]
    sustainability_preferences: Dict[str, Any]
    backup_plans: List[Dict[str, Any]]
    risk_assessments: List[Dict[str, Any]]

# Helper type definitions for complex nested structures
class WorkflowStep(TypedDict):
    """Individual workflow step tracking"""
    step_id: str
    step_name: str
    agent_type: AgentType
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time_ms: Optional[int]
    memory_usage: Optional[float]

class AgentCapability(TypedDict):
    """Agent capability definition"""
    agent_type: AgentType
    capabilities: List[str]
    required_tools: List[str]
    performance_metrics: Dict[str, float]
    last_used: Optional[str]

class SystemMetrics(TypedDict):
    """System performance metrics"""
    total_execution_time: float
    memory_peak_usage: float
    agent_performance: Dict[str, float]
    error_rate: float
    user_satisfaction_score: Optional[float]

# Validation schemas
class ValidationRule(TypedDict):
    """Validation rule definition"""
    field: str
    rule_type: str
    parameters: Dict[str, Any]
    error_message: str
    severity: PriorityLevel

class ValidationResult(TypedDict):
    """Validation result"""
    field: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

# Export the main state for use in graph.py
__all__ = [
    'EventPlanState',
    'EventType',
    'EventStatus', 
    'AgentType',
    'PriorityLevel',
    'ContactInfo',
    'Address',
    'EventIdea',
    'LocationSuggestion',
    'VendorService',
    'ScheduleItem',
    'InvitationDetails',
    'ReviewFeedback',
    'ExportSettings',
    'EmailSettings',
    'WorkflowStep',
    'AgentCapability',
    'SystemMetrics',
    'ValidationRule',
    'ValidationResult'
]