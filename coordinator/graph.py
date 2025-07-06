import asyncio
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime, timedelta
import json
from enum import Enum

# LangGraph & LangChain imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_community.chat_models import ChatOllama

# Agent imports
from agents.idea_agent import IdeaAgent
from agents.location_agent import LocationAgent
from agents.vendor_agent import VendorResearchAgent
from agents.scheduler_agent import SchedulerAgent
from agents.invitation_agent import InvitationAgent
from agents.reviewer_agent import ReviewerAgent
from agents.email_agent import EmailAgent

# Utility imports
from utils.ics_generator import generate_ics
from utils.invitation_utils import (
    split_invitation_output,
    create_html_fallback,
    validate_invitation_output,
    extract_invite_metadata
)
from utils.markdown_formatter import format_markdown_output
from utils.pdf_helper import PDFHelper
from utils.scheduler_utils import SchedulerUtils
from utils.review_utils import ReviewUtils
from utils.validator import Validator
from utils.venue_map_tool import VenueMapTool
from utils.vendor_map_tool import VendorMapTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowStage(Enum):
    """Workflow stages for the event planning process"""
    INITIALIZED = "initialized"
    IDEA_GENERATION = "idea_generation"
    IDEA_SELECTION = "idea_selection"
    LOCATION_RESEARCH = "location_research"
    LOCATION_SELECTION = "location_selection"
    VENDOR_RESEARCH = "vendor_research"
    VENDOR_SELECTION = "vendor_selection"
    SCHEDULE_PLANNING = "schedule_planning"
    SCHEDULE_APPROVAL = "schedule_approval"
    INVITATION_CREATION = "invitation_creation"
    REVIEW_PHASE = "review_phase"
    REVISION_REQUESTED = "revision_requested"
    EXPORT_PREPARATION = "export_preparation"
    EMAIL_SENDING = "email_sending"
    COMPLETED = "completed"
    ERROR = "error"

class EventPlanState(TypedDict):
    """
    Comprehensive state schema for the event planning workflow
    This represents the MCP Context that flows between all agents
    """
    # Core conversation flow
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Workflow management
    current_stage: WorkflowStage
    workflow_history: List[Dict[str, Any]]
    user_inputs: Dict[str, Any]
    agent_outputs: Dict[str, Any]
    errors: List[Dict[str, Any]]
    
    # Event core details
    event_type: Optional[str]
    event_theme: Optional[str]
    budget: Optional[float]
    estimated_guests: Optional[int]
    preferred_date: Optional[str]
    preferred_time: Optional[str]
    duration_hours: Optional[int]
    
    # Location & Venue
    location_preferences: Dict[str, Any]
    suggested_locations: List[Dict[str, Any]]
    selected_location: Optional[Dict[str, Any]]
    venue_requirements: Dict[str, Any]
    
    # Vendor & Services
    vendor_categories: List[str]
    vendor_research_results: Dict[str, List[Dict[str, Any]]]
    selected_vendors: Dict[str, Dict[str, Any]]
    service_requirements: Dict[str, Any]
    
    # Schedule & Timeline
    event_schedule: Dict[str, Any]
    timeline_breakdown: List[Dict[str, Any]]
    schedule_approved: bool
    schedule_revisions: List[Dict[str, Any]]
    
    # Invitation & Communication
    invitation_content: Dict[str, Any]
    invitation_style: str
    guest_list: List[Dict[str, Any]]
    rsvp_details: Dict[str, Any]
    
    # Review & Quality Control
    review_feedback: List[Dict[str, Any]]
    revision_requests: List[Dict[str, Any]]
    quality_score: Optional[float]
    approval_status: str
    
    # Export & Distribution
    export_formats: List[str]
    generated_files: Dict[str, str]
    email_settings: Dict[str, Any]
    distribution_status: Dict[str, Any]
    
    # Context & Memory
    user_preferences: Dict[str, Any]
    conversation_context: List[Dict[str, Any]]
    agent_memories: Dict[str, Any]
    
    # Streaming & UI
    streaming_enabled: bool
    ui_updates: List[Dict[str, Any]]
    progress_percentage: int

class EventPlanningGraph:
    """
    The Core Agentic Brain - Multi-Agent Event Planning Orchestrator
    
    This class implements the MCP (Model-Context-Protocol) pattern:
    - Model: AI Agents with specialized capabilities
    - Context: Shared EventPlanState across all agents
    - Protocol: LangGraph workflow orchestration
    """
    
    def __init__(self, 
                 model_name: str = "phi3",
                 ollama_base_url: str = "http://localhost:11434",
                 memory_saver: Optional[MemorySaver] = None,
                 streaming: bool = True):
        """Initialize the EventPlanningGraph with all components"""
        
        self.model_name = model_name
        self.streaming = streaming
        
        # Initialize LLM
        self.llm = ChatOllama(
            model=model_name,
            base_url=ollama_base_url,
            temperature=0.7,
            num_predict=2048,
        )
        
        # Initialize memory for conversation persistence
        self.memory = memory_saver or MemorySaver()
        
        # Initialize all agents with shared LLM
        self._initialize_agents()
        
        # Initialize utilities
        self._initialize_utilities()
        
        # Build the workflow graph
        self.graph = self._build_workflow_graph()
        
        logger.info("EventPlanningGraph initialized successfully")
    
    def _initialize_agents(self):
        """Initialize all specialized AI agents"""
        self.agents = {
            'idea': IdeaAgent(llm=self.llm),
            'location': LocationAgent(llm=self.llm),
            'vendor_research': VendorResearchAgent(llm=self.llm),
            'scheduler': SchedulerAgent(llm=self.llm),
            'invitation': InvitationAgent(llm=self.llm),
            'reviewer': ReviewerAgent(llm=self.llm),
            'email': EmailAgent(llm=self.llm)
        }
        
        logger.info(f"Initialized {len(self.agents)} specialized agents")
    
    def _initialize_utilities(self):
        """Initialize all utility tools and helpers"""
        self.utils = {
            'ics': generate_ics,
            'invitation': {
                'split_output': split_invitation_output,
                'create_html_fallback': create_html_fallback,
                'validate_output': validate_invitation_output,
                'extract_metadata': extract_invite_metadata
            },
            'markdown': format_markdown_output,
            'pdf': PDFHelper(),
            'scheduler': SchedulerUtils(),
            'review': ReviewUtils(),
            'validator': Validator(),
            'venue_map': VenueMapTool(),
            'vendor_map': VendorMapTool()
        }
        
        logger.info(f"Initialized {len(self.utils)} utility tools")
    
    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the complex LangGraph workflow that orchestrates all agents
        This is the Protocol layer of the MCP architecture
        """
        
        # Create the state graph
        workflow = StateGraph(EventPlanState)
        
        # Add all agent nodes
        workflow.add_node("initialize_workflow", self._initialize_workflow_node)
        workflow.add_node("idea_generation", self._idea_generation_node)
        workflow.add_node("idea_selection", self._idea_selection_node)
        workflow.add_node("location_research", self._location_research_node)
        workflow.add_node("location_selection", self._location_selection_node)
        workflow.add_node("vendor_research", self._vendor_research_node)
        workflow.add_node("vendor_selection", self._vendor_selection_node)
        workflow.add_node("schedule_planning", self._schedule_planning_node)
        workflow.add_node("schedule_approval", self._schedule_approval_node)
        workflow.add_node("invitation_creation", self._invitation_creation_node)
        workflow.add_node("review_phase", self._review_phase_node)
        workflow.add_node("handle_revisions", self._handle_revisions_node)
        workflow.add_node("export_preparation", self._export_preparation_node)
        workflow.add_node("email_distribution", self._email_distribution_node)
        workflow.add_node("workflow_completion", self._workflow_completion_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Define the workflow edges and conditional routing
        self._define_workflow_edges(workflow)
        
        # Set entry point
        workflow.set_entry_point("initialize_workflow")
        
        # Compile with memory
        compiled_graph = workflow.compile(checkpointer=self.memory)
        
        logger.info("Workflow graph compiled successfully")
        return compiled_graph
    
    def _define_workflow_edges(self, workflow: StateGraph):
        """Define the complex conditional routing between nodes"""
        
        # Initialize -> Idea Generation
        workflow.add_edge("initialize_workflow", "idea_generation")
        
        # Idea Generation -> Selection (with user interaction)
        workflow.add_conditional_edges(
            "idea_generation",
            self._route_after_idea_generation,
            {
                "user_selection": "idea_selection",
                "regenerate": "idea_generation",
                "error": "error_handler"
            }
        )
        
        # Idea Selection -> Location Research
        workflow.add_edge("idea_selection", "location_research")
        
        # Location Research -> Selection
        workflow.add_conditional_edges(
            "location_research",
            self._route_after_location_research,
            {
                "user_selection": "location_selection",
                "research_more": "location_research",
                "error": "error_handler"
            }
        )
        
        # Location Selection -> Vendor Research
        workflow.add_edge("location_selection", "vendor_research")
        
        # Vendor Research -> Selection
        workflow.add_conditional_edges(
            "vendor_research",
            self._route_after_vendor_research,
            {
                "user_selection": "vendor_selection",
                "research_more": "vendor_research",
                "error": "error_handler"
            }
        )
        
        # Vendor Selection -> Schedule Planning
        workflow.add_edge("vendor_selection", "schedule_planning")
        
        # Schedule Planning -> Approval
        workflow.add_conditional_edges(
            "schedule_planning",
            self._route_after_schedule_planning,
            {
                "user_approval": "schedule_approval",
                "needs_revision": "schedule_planning",
                "error": "error_handler"
            }
        )
        
        # Schedule Approval -> Invitation Creation
        workflow.add_edge("schedule_approval", "invitation_creation")
        
        # Invitation Creation -> Review
        workflow.add_edge("invitation_creation", "review_phase")
        
        # Review Phase -> Complex routing
        workflow.add_conditional_edges(
            "review_phase",
            self._route_after_review,
            {
                "approved": "export_preparation",
                "needs_revision": "handle_revisions",
                "major_changes": "idea_generation",
                "error": "error_handler"
            }
        )
        
        # Handle Revisions -> Back to appropriate stage
        workflow.add_conditional_edges(
            "handle_revisions",
            self._route_after_revisions,
            {
                "idea_revision": "idea_generation",
                "location_revision": "location_research",
                "vendor_revision": "vendor_research",
                "schedule_revision": "schedule_planning",
                "invitation_revision": "invitation_creation",
                "review_again": "review_phase"
            }
        )
        
        # Export Preparation -> Email Distribution
        workflow.add_conditional_edges(
            "export_preparation",
            self._route_after_export,
            {
                "send_email": "email_distribution",
                "skip_email": "workflow_completion",
                "error": "error_handler"
            }
        )
        
        # Email Distribution -> Completion
        workflow.add_edge("email_distribution", "workflow_completion")
        
        # Completion and Error handling
        workflow.add_edge("workflow_completion", END)
        workflow.add_edge("error_handler", END)
    
    # Node Implementation Methods
    async def _initialize_workflow_node(self, state: EventPlanState) -> EventPlanState:
        """Initialize the workflow with user input and context"""
        logger.info("Initializing workflow...")
        
        try:
            state["current_stage"] = WorkflowStage.INITIALIZED
            state["workflow_history"] = []
            state["agent_outputs"] = {}
            state["errors"] = []
            state["progress_percentage"] = 0
            
            # Add system initialization message
            init_message = SystemMessage(
                content="EventPlanGenie workflow initialized. Ready to help you plan the perfect event!"
            )
            state["messages"].append(init_message)
            
            # Log workflow start
            self._log_workflow_step(state, "workflow_initialized", {
                "timestamp": datetime.now().isoformat(),
                "user_inputs": state.get("user_inputs", {})
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in workflow initialization: {str(e)}")
            state["errors"].append({
                "stage": "initialization",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            state["current_stage"] = WorkflowStage.ERROR
            return state
    
    async def _idea_generation_node(self, state: EventPlanState) -> EventPlanState:
        """Generate creative event ideas using IdeaAgent"""
        logger.info("Generating event ideas...")
        
        try:
            state["current_stage"] = WorkflowStage.IDEA_GENERATION
            state["progress_percentage"] = 15
            
            # Prepare context for IdeaAgent
            idea_context = {
                "event_type": state.get("event_type"),
                "budget": state.get("budget"),
                "guests": state.get("estimated_guests"),
                "preferences": state.get("user_preferences", {})
            }
            
            # Generate ideas using the specialized agent
            idea_results = await self.agents['idea'].generate_ideas(idea_context)
            
            # Store results in state
            state["agent_outputs"]["idea_generation"] = idea_results
            state["suggested_ideas"] = idea_results.get("ideas", [])
            
            # Add AI message with ideas
            ideas_message = AIMessage(
                content=f"I've generated {len(state['suggested_ideas'])} creative event ideas for you to choose from!"
            )
            state["messages"].append(ideas_message)
            
            self._log_workflow_step(state, "ideas_generated", {
                "ideas_count": len(state["suggested_ideas"]),
                "agent": "IdeaAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in idea generation: {str(e)}")
            return self._handle_node_error(state, "idea_generation", e)
    
    async def _idea_selection_node(self, state: EventPlanState) -> EventPlanState:
        """Handle user selection of event idea"""
        logger.info("Processing idea selection...")
        
        try:
            state["current_stage"] = WorkflowStage.IDEA_SELECTION
            state["progress_percentage"] = 25
            
            # Get user's selected idea (this would come from frontend interaction)
            selected_idea = state.get("selected_idea")
            
            if not selected_idea:
                # If no selection yet, wait for user input
                state["waiting_for_user_input"] = True
                state["input_type"] = "idea_selection"
                return state
            
            # Store the selected idea
            state["agent_outputs"]["idea_selection"] = {"selected_idea": selected_idea}
            
            # Add confirmation message
            selection_message = AIMessage(
                content=f"Great choice! I'll now proceed with planning your {selected_idea.get('title', 'event')}."
            )
            state["messages"].append(selection_message)
            
            self._log_workflow_step(state, "idea_selected", {
                "selected_idea": selected_idea,
                "agent": "IdeaAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in idea selection: {str(e)}")
            return self._handle_node_error(state, "idea_selection", e)
    
    async def _location_research_node(self, state: EventPlanState) -> EventPlanState:
        """Research locations using LocationAgent"""
        logger.info("Researching locations...")
        
        try:
            state["current_stage"] = WorkflowStage.LOCATION_RESEARCH
            state["progress_percentage"] = 35
            
            # Prepare context for LocationAgent
            location_context = {
                "event_type": state.get("event_type"),
                "selected_idea": state.get("selected_idea"),
                "budget": state.get("budget"),
                "guests": state.get("estimated_guests"),
                "location_preferences": state.get("location_preferences", {})
            }
            
            # Research locations
            location_results = await self.agents['location'].research_locations(location_context)
            
            # Store results
            state["agent_outputs"]["location_research"] = location_results
            state["suggested_locations"] = location_results.get("locations", [])
            
            # Enhance with map data
            if self.utils['venue_map']:
                for location in state["suggested_locations"]:
                    try:
                        map_data = await self.utils['venue_map'].get_venue_details(location)
                        location.update(map_data)
                    except Exception as e:
                        logger.warning(f"Could not get map data for location: {e}")
            
            # Add AI message
            location_message = AIMessage(
                content=f"I found {len(state['suggested_locations'])} potential venues for your event!"
            )
            state["messages"].append(location_message)
            
            self._log_workflow_step(state, "locations_researched", {
                "locations_count": len(state["suggested_locations"]),
                "agent": "LocationAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in location research: {str(e)}")
            return self._handle_node_error(state, "location_research", e)
    
    async def _location_selection_node(self, state: EventPlanState) -> EventPlanState:
        """Handle user selection of location"""
        logger.info("Processing location selection...")
        
        try:
            state["current_stage"] = WorkflowStage.LOCATION_SELECTION
            state["progress_percentage"] = 45
            
            # Get user's selected location
            selected_location = state.get("selected_location")
            
            if not selected_location:
                # If no selection yet, wait for user input
                state["waiting_for_user_input"] = True
                state["input_type"] = "location_selection"
                return state
            
            # Store the selected location
            state["agent_outputs"]["location_selection"] = {"selected_location": selected_location}
            
            # Add confirmation message
            selection_message = AIMessage(
                content=f"Perfect! I've noted {selected_location.get('name', 'your chosen venue')} as the location."
            )
            state["messages"].append(selection_message)
            
            self._log_workflow_step(state, "location_selected", {
                "selected_location": selected_location,
                "agent": "LocationAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in location selection: {str(e)}")
            return self._handle_node_error(state, "location_selection", e)
    
    async def _vendor_research_node(self, state: EventPlanState) -> EventPlanState:
        """Research vendors using VendorResearchAgent"""
        logger.info("Researching vendors...")
        
        try:
            state["current_stage"] = WorkflowStage.VENDOR_RESEARCH
            state["progress_percentage"] = 55
            
            # Prepare context for VendorResearchAgent
            vendor_context = {
                "event_type": state.get("event_type"),
                "selected_idea": state.get("selected_idea"),
                "selected_location": state.get("selected_location"),
                "budget": state.get("budget"),
                "guests": state.get("estimated_guests"),
                "vendor_categories": state.get("vendor_categories", ["catering", "photography", "entertainment"])
            }
            
            # Research vendors
            vendor_results = await self.agents['vendor_research'].research_vendors(vendor_context)
            
            # Store results
            state["agent_outputs"]["vendor_research"] = vendor_results
            state["vendor_research_results"] = vendor_results.get("vendors", {})
            
            # Add AI message
            vendor_message = AIMessage(
                content=f"I've researched vendors across {len(state['vendor_research_results'])} categories for your event!"
            )
            state["messages"].append(vendor_message)
            
            self._log_workflow_step(state, "vendors_researched", {
                "vendor_categories": len(state["vendor_research_results"]),
                "agent": "VendorResearchAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in vendor research: {str(e)}")
            return self._handle_node_error(state, "vendor_research", e)
    
    async def _vendor_selection_node(self, state: EventPlanState) -> EventPlanState:
        """Handle user selection of vendors"""
        logger.info("Processing vendor selection...")
        
        try:
            state["current_stage"] = WorkflowStage.VENDOR_SELECTION
            state["progress_percentage"] = 65
            
            # Get user's selected vendors
            selected_vendors = state.get("selected_vendors", {})
            
            if not selected_vendors:
                # If no selection yet, wait for user input
                state["waiting_for_user_input"] = True
                state["input_type"] = "vendor_selection"
                return state
            
            # Store the selected vendors
            state["agent_outputs"]["vendor_selection"] = {"selected_vendors": selected_vendors}
            
            # Add confirmation message
            selection_message = AIMessage(
                content=f"Excellent! I've confirmed your vendor selections across {len(selected_vendors)} categories."
            )
            state["messages"].append(selection_message)
            
            self._log_workflow_step(state, "vendors_selected", {
                "selected_vendors": selected_vendors,
                "agent": "VendorResearchAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in vendor selection: {str(e)}")
            return self._handle_node_error(state, "vendor_selection", e)
    
    async def _schedule_planning_node(self, state: EventPlanState) -> EventPlanState:
        """Plan event schedule using SchedulerAgent"""
        logger.info("Planning event schedule...")
        
        try:
            state["current_stage"] = WorkflowStage.SCHEDULE_PLANNING
            state["progress_percentage"] = 75
            
            # Prepare context for SchedulerAgent
            schedule_context = {
                "event_type": state.get("event_type"),
                "selected_idea": state.get("selected_idea"),
                "selected_location": state.get("selected_location"),
                "selected_vendors": state.get("selected_vendors", {}),
                "preferred_date": state.get("preferred_date"),
                "preferred_time": state.get("preferred_time"),
                "duration_hours": state.get("duration_hours", 4),
                "estimated_guests": state.get("estimated_guests")
            }
            
            # Plan schedule
            schedule_results = await self.agents['scheduler'].plan_schedule(schedule_context)
            
            # Store results
            state["agent_outputs"]["schedule_planning"] = schedule_results
            state["event_schedule"] = schedule_results.get("schedule", {})
            state["timeline_breakdown"] = schedule_results.get("timeline", [])
            
            # Add AI message
            schedule_message = AIMessage(
                content=f"I've created a detailed schedule for your event with {len(state['timeline_breakdown'])} activities!"
            )
            state["messages"].append(schedule_message)
            
            self._log_workflow_step(state, "schedule_planned", {
                "timeline_items": len(state["timeline_breakdown"]),
                "agent": "SchedulerAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in schedule planning: {str(e)}")
            return self._handle_node_error(state, "schedule_planning", e)
    
    async def _schedule_approval_node(self, state: EventPlanState) -> EventPlanState:
        """Handle user approval of schedule"""
        logger.info("Processing schedule approval...")
        
        try:
            state["current_stage"] = WorkflowStage.SCHEDULE_APPROVAL
            state["progress_percentage"] = 80
            
            # Get user's approval status
            schedule_approved = state.get("schedule_approved", False)
            
            if not schedule_approved:
                # If not approved yet, wait for user input
                state["waiting_for_user_input"] = True
                state["input_type"] = "schedule_approval"
                return state
            
            # Store approval
            state["agent_outputs"]["schedule_approval"] = {"approved": True}
            
            # Add confirmation message
            approval_message = AIMessage(
                content="Great! Your event schedule is approved. Now let's create the invitations!"
            )
            state["messages"].append(approval_message)
            
            self._log_workflow_step(state, "schedule_approved", {
                "approved": True,
                "agent": "SchedulerAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in schedule approval: {str(e)}")
            return self._handle_node_error(state, "schedule_approval", e)
    
    async def _invitation_creation_node(self, state: EventPlanState) -> EventPlanState:
        """Create invitations using InvitationAgent"""
        logger.info("Creating invitations...")
        
        try:
            state["current_stage"] = WorkflowStage.INVITATION_CREATION
            state["progress_percentage"] = 85
            
            # Prepare context for InvitationAgent
            invitation_context = {
                "event_type": state.get("event_type"),
                "selected_idea": state.get("selected_idea"),
                "selected_location": state.get("selected_location"),
                "event_schedule": state.get("event_schedule", {}),
                "invitation_style": state.get("invitation_style", "modern"),
                "guest_list": state.get("guest_list", []),
                "rsvp_details": state.get("rsvp_details", {})
            }
            
            # Create invitations
            invitation_results = await self.agents['invitation'].create_invitations(invitation_context)
            
            # Store results
            state["agent_outputs"]["invitation_creation"] = invitation_results
            state["invitation_content"] = invitation_results.get("invitation", {})
            
            # Add AI message
            invitation_message = AIMessage(
                content="I've created beautiful invitations for your event!"
            )
            state["messages"].append(invitation_message)
            
            self._log_workflow_step(state, "invitations_created", {
                "invitation_ready": True,
                "agent": "InvitationAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in invitation creation: {str(e)}")
            return self._handle_node_error(state, "invitation_creation", e)
    
    async def _review_phase_node(self, state: EventPlanState) -> EventPlanState:
        """Review the complete event plan using ReviewerAgent"""
        logger.info("Reviewing event plan...")
        
        try:
            state["current_stage"] = WorkflowStage.REVIEW_PHASE
            state["progress_percentage"] = 90
            
            # Prepare context for ReviewerAgent
            review_context = {
                "selected_idea": state.get("selected_idea"),
                "selected_location": state.get("selected_location"),
                "selected_vendors": state.get("selected_vendors", {}),
                "event_schedule": state.get("event_schedule", {}),
                "invitation_content": state.get("invitation_content", {}),
                "budget": state.get("budget"),
                "user_preferences": state.get("user_preferences", {})
            }
            
            # Review the plan
            review_results = await self.agents['reviewer'].review_plan(review_context)
            
            # Store results
            state["agent_outputs"]["review_phase"] = review_results
            state["review_feedback"] = review_results.get("feedback", [])
            state["quality_score"] = review_results.get("quality_score", 0.0)
            state["approval_status"] = review_results.get("status", "pending")
            
            # Add AI message
            review_message = AIMessage(
                content=f"I've reviewed your complete event plan! Quality score: {state['quality_score']}/10"
            )
            state["messages"].append(review_message)
            
            self._log_workflow_step(state, "plan_reviewed", {
                "quality_score": state["quality_score"],
                "status": state["approval_status"],
                "agent": "ReviewerAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in review phase: {str(e)}")
            return self._handle_node_error(state, "review_phase", e)
    
    async def _handle_revisions_node(self, state: EventPlanState) -> EventPlanState:
        """Handle revision requests"""
        logger.info("Handling revision requests...")
        
        try:
            state["current_stage"] = WorkflowStage.REVISION_REQUESTED
            
            # Get revision requests
            revision_requests = state.get("revision_requests", [])
            
            if not revision_requests:
                # No specific revisions, go back to review
                return state
            
            # Process each revision request
            for request in revision_requests:
                revision_type = request.get("type")
                if revision_type == "idea":
                    state["needs_idea_revision"] = True
                elif revision_type == "location":
                    state["needs_location_revision"] = True
                elif revision_type == "vendor":
                    state["needs_vendor_revision"] = True
                elif revision_type == "schedule":
                    state["needs_schedule_revision"] = True
                elif revision_type == "invitation":
                    state["needs_invitation_revision"] = True
            
            # Store revision handling
            state["agent_outputs"]["handle_revisions"] = {"revisions_processed": len(revision_requests)}
            
            # Add AI message
            revision_message = AIMessage(
                content=f"I'm processing {len(revision_requests)} revision requests to improve your event plan."
            )
            state["messages"].append(revision_message)
            
            self._log_workflow_step(state, "revisions_handled", {
                "revision_count": len(revision_requests),
                "agent": "ReviewerAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in handling revisions: {str(e)}")
            return self._handle_node_error(state, "handle_revisions", e)
    
    async def _export_preparation_node(self, state: EventPlanState) -> EventPlanState:
        """Prepare exports and final deliverables"""
        logger.info("Preparing exports...")
        
        try:
            state["current_stage"] = WorkflowStage.EXPORT_PREPARATION
            state["progress_percentage"] = 95
            
            # Prepare export formats
            export_formats = state.get("export_formats", ["pdf", "ics", "html"])
            generated_files = {}
            
            # Generate ICS calendar file
            if "ics" in export_formats:
                try:
                    ics_content = self.utils['ics'](
                        event_title=state.get("selected_idea", {}).get("title", "Event"),
                        event_date=state.get("preferred_date"),
                        event_time=state.get("preferred_time"),
                        location=state.get("selected_location", {}).get("name", ""),
                        description=state.get("selected_idea", {}).get("description", "")
                    )
                    generated_files["ics"] = ics_content
                except Exception as e:
                    logger.warning(f"Could not generate ICS: {e}")
            
            # Generate PDF summary
            if "pdf" in export_formats:
                try:
                    pdf_content = await self.utils['pdf'].generate_event_summary(state)
                    generated_files["pdf"] = pdf_content
                except Exception as e:
                    logger.warning(f"Could not generate PDF: {e}")
            
            # Generate HTML invitation
            if "html" in export_formats:
                try:
                    html_content = self.utils['invitation']['create_html_fallback'](
                        state.get("invitation_content", {})
                    )
                    generated_files["html"] = html_content
                except Exception as e:
                    logger.warning(f"Could not generate HTML: {e}")
            
            # Store generated files
            state["generated_files"] = generated_files
            state["agent_outputs"]["export_preparation"] = {"files_generated": len(generated_files)}
            
            # Add AI message
            export_message = AIMessage(
                content=f"I've prepared {len(generated_files)} files for your event: {', '.join(generated_files.keys())}"
            )
            state["messages"].append(export_message)
            
            self._log_workflow_step(state, "exports_prepared", {
                "files_generated": len(generated_files),
                "formats": list(generated_files.keys())
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in export preparation: {str(e)}")
            return self._handle_node_error(state, "export_preparation", e)
    
    async def _email_distribution_node(self, state: EventPlanState) -> EventPlanState:
        """Handle email distribution using EmailAgent"""
        logger.info("Distributing emails...")
        
        try:
            state["current_stage"] = WorkflowStage.EMAIL_SENDING
            state["progress_percentage"] = 98
            
            # Prepare context for EmailAgent
            email_context = {
                "invitation_content": state.get("invitation_content", {}),
                "guest_list": state.get("guest_list", []),
                "email_settings": state.get("email_settings", {}),
                "generated_files": state.get("generated_files", {})
            }
            
            # Send emails
            email_results = await self.agents['email'].send_invitations(email_context)
            
            # Store results
            state["agent_outputs"]["email_distribution"] = email_results
            state["distribution_status"] = email_results.get("status", {})
            
            # Add AI message
            email_message = AIMessage(
                content=f"Invitations sent to {email_results.get('sent_count', 0)} recipients!"
            )
            state["messages"].append(email_message)
            
            self._log_workflow_step(state, "emails_sent", {
                "sent_count": email_results.get("sent_count", 0),
                "agent": "EmailAgent"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in email distribution: {str(e)}")
            return self._handle_node_error(state, "email_distribution", e)
    
    async def _workflow_completion_node(self, state: EventPlanState) -> EventPlanState:
        """Complete the workflow"""
        logger.info("Completing workflow...")
        
        try:
            state["current_stage"] = WorkflowStage.COMPLETED
            state["progress_percentage"] = 100
            
            # Add completion message
            completion_message = AIMessage(
                content="🎉 Your event planning is complete! All files have been generated and invitations sent."
            )
            state["messages"].append(completion_message)
            
            self._log_workflow_step(state, "workflow_completed", {
                "total_steps": len(state.get("workflow_history", [])),
                "success": True
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in workflow completion: {str(e)}")
            return self._handle_node_error(state, "workflow_completion", e)
    
    async def _error_handler_node(self, state: EventPlanState) -> EventPlanState:
        """Handle errors in the workflow"""
        logger.info("Handling workflow errors...")
        
        try:
            state["current_stage"] = WorkflowStage.ERROR
            
            # Get the latest error
            errors = state.get("errors", [])
            if errors:
                latest_error = errors[-1]
                
                # Add error message
                error_message = AIMessage(
                    content=f"I encountered an error: {latest_error.get('error', 'Unknown error')}. Let me try to recover."
                )
                state["messages"].append(error_message)
            
            self._log_workflow_step(state, "error_handled", {
                "error_count": len(errors),
                "latest_error": errors[-1] if errors else None
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")
            # Even the error handler failed, so just return the state
            return state
    
    # Routing Methods
    def _route_after_idea_generation(self, state: EventPlanState) -> str:
        """Determine routing after idea generation"""
        if state.get("errors"):
            return "error"
        elif state.get("user_wants_regeneration"):
            return "regenerate"
        else:
            return "user_selection"
    
    def _route_after_location_research(self, state: EventPlanState) -> str:
        """Determine routing after location research"""
        if state.get("errors"):
            return "error"
        elif state.get("needs_more_research"):
            return "research_more"
        else:
            return "user_selection"
    
    def _route_after_vendor_research(self, state: EventPlanState) -> str:
        """Determine routing after vendor research"""
        if state.get("errors"):
            return "error"
        elif state.get("needs_more_research"):
            return "research_more"
        else:
            return "user_selection"
    
    def _route_after_schedule_planning(self, state: EventPlanState) -> str:
        """Determine routing after schedule planning"""
        if state.get("errors"):
            return "error"
        elif state.get("needs_schedule_revision"):
            return "needs_revision"
        else:
            return "user_approval"
    
    def _route_after_review(self, state: EventPlanState) -> str:
        """Determine routing after review phase"""
        if state.get("errors"):
            return "error"
        
        approval_status = state.get("approval_status", "pending")
        quality_score = state.get("quality_score", 0.0)
        
        if approval_status == "approved" and quality_score >= 8.0:
            return "approved"
        elif approval_status == "needs_major_changes":
            return "major_changes"
        else:
            return "needs_revision"
    
    def _route_after_revisions(self, state: EventPlanState) -> str:
        """Determine routing after handling revisions"""
        if state.get("needs_idea_revision"):
            return "idea_revision"
        elif state.get("needs_location_revision"):
            return "location_revision"
        elif state.get("needs_vendor_revision"):
            return "vendor_revision"
        elif state.get("needs_schedule_revision"):
            return "schedule_revision"
        elif state.get("needs_invitation_revision"):
            return "invitation_revision"
        else:
            return "review_again"
    
    def _route_after_export(self, state: EventPlanState) -> str:
        """Determine routing after export preparation"""
        if state.get("errors"):
            return "error"
        elif state.get("send_emails", True):
            return "send_email"
        else:
            return "skip_email"
    
    # Utility Methods
    def _log_workflow_step(self, state: EventPlanState, step: str, data: Dict[str, Any]):
        """Log workflow steps for debugging and monitoring"""
        log_entry = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "stage": state["current_stage"].value if state.get("current_stage") else "unknown",
            "data": data
        }
        
        if "workflow_history" not in state:
            state["workflow_history"] = []
        
        state["workflow_history"].append(log_entry)
        logger.info(f"Workflow step: {step} - {data}")
    
    def _handle_node_error(self, state: EventPlanState, node_name: str, error: Exception) -> EventPlanState:
        """Handle errors that occur in workflow nodes"""
        error_info = {
            "node": node_name,
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "stage": state.get("current_stage", "unknown")
        }
        
        if "errors" not in state:
            state["errors"] = []
        
        state["errors"].append(error_info)
        state["current_stage"] = WorkflowStage.ERROR
        
        error_message = AIMessage(
            content=f"I encountered an error in {node_name}. Let me try to recover and continue."
        )
        
        if "messages" not in state:
            state["messages"] = []
        
        state["messages"].append(error_message)
        
        logger.error(f"Node error in {node_name}: {str(error)}")
        return state
    
    async def plan_event(self, 
                        user_input: Dict[str, Any], 
                        config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Main entry point for event planning
        This orchestrates the entire multi-agent workflow
        """
        
        # Initialize state with user input
        initial_state = EventPlanState(
            messages=[HumanMessage(content=json.dumps(user_input))],
            current_stage=WorkflowStage.INITIALIZED,
            user_inputs=user_input,
            streaming_enabled=self.streaming,
            workflow_history=[],
            agent_outputs={},
            errors=[],
            progress_percentage=0,
            **{k: v for k, v in user_input.items() if k in EventPlanState.__annotations__}
        )
        
        try:
            # Execute the workflow
            if self.streaming:
                result = await self._execute_streaming_workflow(initial_state, config)
            else:
                result = await self.graph.ainvoke(initial_state, config)
            
            return self._format_final_result(result)
            
        except Exception as e:
            logger.error(f"Error in event planning workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "stage": initial_state.get("current_stage", "unknown")
            }
    
    async def _execute_streaming_workflow(self, 
                                          initial_state: EventPlanState, 
                                          config: Optional[RunnableConfig]) -> EventPlanState:
        """Execute workflow with streaming capabilities"""
        
        result_state = initial_state
        
        async for chunk in self.graph.astream(initial_state, config):
            logger.info(f"Streaming chunk: {chunk}")
            
            for node_name, node_result in chunk.items():
                if isinstance(node_result, dict):
                    result_state.update(node_result)
                    
        return result_state
    
    async def _execute_streaming_workflow_generator(self, 
                                                    initial_state: EventPlanState, 
                                                    config: Optional[RunnableConfig]):
        """Execute workflow with streaming capabilities - generator version"""
        
        result_state = initial_state
        
        async for chunk in self.graph.astream(initial_state, config):
            yield chunk
        
        for node_name, node_result in chunk.items():
            if isinstance(node_result, dict):
                result_state.update(node_result)
    
    
    def _format_final_result(self, state: EventPlanState) -> Dict[str, Any]:
        """Format the final workflow result for the frontend"""
        
        return {
            "success": state["current_stage"] == WorkflowStage.COMPLETED,
            "stage": state["current_stage"].value,
            "progress": state.get("progress_percentage", 0),
            "event_plan": {
                "idea": state.get("selected_idea"),
                "location": state.get("selected_location"),
                "vendors": state.get("selected_vendors"),
                "schedule": state.get("event_schedule"),
                "invitation": state.get("invitation_content")
            },
            "generated_files": state.get("generated_files", {}),
            "workflow_history": state.get("workflow_history", []),
            "errors": state.get("errors", []),
            "messages": [msg.content for msg in state.get("messages", [])]
        }

# Factory function for easy instantiation
def create_event_planning_graph(**kwargs) -> EventPlanningGraph:
    """Factory function to create and configure the EventPlanningGraph"""
    return EventPlanningGraph(**kwargs)

# Example usage and testing
if __name__ == "__main__":
    async def test_workflow():
        """Test the event planning workflow"""
        
        graph = create_event_planning_graph()
        
        test_input = {
            "event_type": "birthday_party",
            "budget": 5000.0,
            "estimated_guests": 25,
            "preferred_date": "2024-06-15",
            "location_preferences": {"indoor": True, "parking": True}
        }
        
        result = await graph.plan_event(test_input)
        print(json.dumps(result, indent=2))
    
    # Run test
    asyncio.run(test_workflow())