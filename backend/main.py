"""
EventPlanGenie Backend - FastAPI Server
Multi-Agent Event Planning System with LangGraph Integration

This FastAPI backend serves as the API layer for the Streamlit frontend,
orchestrating the complex multi-agent workflow through the graph.py brain.
"""

import asyncio
import logging
import json
import uuid
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator

# Core system imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coordinator.graph import EventPlanningGraph, create_event_planning_graph
from utils.validator import Validator
from agents.email_agent import EmailAgent
from utils.pdf_helper import PDFHelper
from utils.ics_generator import ICSGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global graph instance
event_graph: Optional[EventPlanningGraph] = None
active_sessions: Dict[str, Dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global event_graph
    
    # Startup
    logger.info("🚀 Starting EventPlanGenie Backend...")
    try:
        event_graph = create_event_planning_graph(
            model_name="gpt-4o-mini",  # Updated to use a more reliable model
            streaming=True
        )
        logger.info("✅ EventPlanningGraph initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize EventPlanningGraph: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down EventPlanGenie Backend...")
    active_sessions.clear()

# FastAPI app initialization
app = FastAPI(
    title="EventPlanGenie API",
    description="Agentic AI Event Planning System with Multi-Agent Workflow",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Pydantic Models
class EventRequest(BaseModel):
    """Event planning request model"""
    event_name: str = Field(..., min_length=3, max_length=100)
    event_type: str = Field(..., min_length=3, max_length=50)
    location: str = Field(..., min_length=3, max_length=100)
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    start_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    end_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    description: str = Field(default="", max_length=500)
    budget_min: float = Field(..., ge=1000, le=10000000)
    budget_max: float = Field(..., ge=1000, le=10000000)
    estimated_guests: int = Field(..., ge=5, le=5000)
    location_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    contact_email: Optional[str] = Field(default=None, pattern=r'^[^@]+@[^@]+\.[^@]+$')

    @field_validator('budget_max')
    @classmethod
    def validate_budget_range(cls, v, info):
        if 'budget_min' in info.data and v < info.data['budget_min']:
            raise ValueError('budget_max must be greater than budget_min')
        return v

class UserSelection(BaseModel):
    """User selection for workflow steps"""
    session_id: str
    selection_type: str  # 'idea', 'location', 'vendor', 'schedule', 'review'
    selected_items: List[Dict[str, Any]]
    feedback: Optional[str] = None
    revision_requests: Optional[List[str]] = None

class WorkflowControl(BaseModel):
    """Workflow control commands"""
    session_id: str
    action: str  # 'pause', 'resume', 'restart', 'cancel'
    reason: Optional[str] = None

class EmailSendRequest(BaseModel):
    session_id: str
    sender_email: str
    sender_password: str
    recipients: List[str]
    subject: Optional[str] = "You're Invited to My Event!"
    custom_message: Optional[str] = None
    attach_pdf: bool = True
    attach_ics: bool = True

class EventResponse(BaseModel):
    """Standardized API response"""
    success: bool
    session_id: Optional[str] = None
    stage: Optional[str] = None
    progress: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# Helper Functions
def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create new one"""
    if session_id and session_id in active_sessions:
        return session_id
    
    new_session_id = str(uuid.uuid4())
    active_sessions[new_session_id] = {
        "created_at": datetime.now(),
        "status": "active",
        "workflow_state": None,
        "progress": 0,
        "stage": "initialized"
    }
    return new_session_id

def validate_session(session_id: str) -> Dict:
    """Validate and return session data"""
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    return active_sessions[session_id]

async def get_auth_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional authentication (for future use)"""
    return {"user_id": "anonymous", "authenticated": False}

# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "EventPlanGenie API",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Detailed health check"""
    try:
        # Check if graph is initialized
        graph_status = "healthy" if event_graph else "unhealthy"
        
        # Check active sessions
        active_count = len(active_sessions)
        
        return {
            "status": "healthy",
            "components": {
                "event_graph": graph_status,
                "active_sessions": active_count,
                "model_connection": "healthy"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/api/v1/events/plan", response_model=EventResponse)
async def start_event_planning(
    request: EventRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_auth_user)
):
    """Start the event planning workflow"""
    try:
        if not event_graph:
            raise HTTPException(status_code=503, detail="Event planning service unavailable")
        
        # Create new session
        session_id = get_or_create_session()
        
        # Prepare input for the graph
        graph_input = {
            "event_name": request.event_name,
            "event_type": request.event_type,
            "location": request.location,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "description": request.description,
            "budget": request.budget_max,
            "budget_min": request.budget_min,
            "estimated_guests": request.estimated_guests,
            "location_preferences": request.location_preferences,
            "user_preferences": request.user_preferences,
            "contact_email": request.contact_email,
            "session_id": session_id
        }
        
        # Store session data
        active_sessions[session_id].update({
            "workflow_input": graph_input,
            "status": "planning",
            "stage": "starting",
            "progress": 5
        })
        
        # Start async workflow
        background_tasks.add_task(run_workflow_async, session_id, graph_input)
        
        return EventResponse(
            success=True,
            session_id=session_id,
            stage="initialized",
            progress=5,
            message="Event planning workflow started successfully",
            data={"input_summary": graph_input}
        )
        
    except Exception as e:
        logger.error(f"Error starting event planning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_workflow_async(session_id: str, graph_input: Dict[str, Any]):
    """Run the workflow asynchronously in background"""
    try:
        logger.info(f"Starting workflow for session {session_id}")
        
        # Update session status
        active_sessions[session_id].update({
            "status": "running",
            "stage": "processing",
            "progress": 10
        })
        
        # Execute the graph workflow
        final_state = {}
        progress_counter = 10
        
        # Check if the graph has a streaming method
        if hasattr(event_graph, 'stream_workflow'):
            # Use streaming if available
            async for state in event_graph.stream_workflow(graph_input):
                # Update progress based on workflow stage
                if "stage" in state:
                    stage = state["stage"]
                    active_sessions[session_id]["stage"] = stage
                    
                    # Update progress based on stage
                    stage_progress = {
                        "idea_generation": 20,
                        "location_research": 40,
                        "vendor_discovery": 60,
                        "schedule_creation": 80,
                        "final_review": 90,
                        "completed": 100
                    }
                    
                    progress = stage_progress.get(stage, progress_counter)
                    active_sessions[session_id]["progress"] = progress
                    progress_counter = min(progress_counter + 5, 95)
                
                final_state.update(state)
                
                # Store intermediate results
                active_sessions[session_id]["current_state"] = final_state
        else:
            # Use synchronous execution
            final_state = event_graph.plan_event(graph_input)
            active_sessions[session_id]["current_state"] = final_state
        
        # Store final result
        active_sessions[session_id].update({
            "workflow_result": final_state,
            "status": "completed" if final_state.get("success", False) else "failed",
            "completed_at": datetime.now(),
            "progress": 100,
            "stage": "completed"
        })
        
        logger.info(f"Workflow completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Workflow error for session {session_id}: {e}")
        active_sessions[session_id].update({
            "status": "error",
            "error": str(e),
            "progress": 0,
            "stage": "error"
        })

@app.get("/api/v1/events/status/{session_id}", response_model=EventResponse)
async def get_workflow_status(session_id: str):
    """Get current workflow status"""
    try:
        session_data = validate_session(session_id)
        
        current_state = session_data.get("current_state", {})
        
        return EventResponse(
            success=True,
            session_id=session_id,
            stage=session_data.get("stage", "unknown"),
            progress=session_data.get("progress", 0),
            data={
                "status": session_data["status"],
                "created_at": session_data["created_at"].isoformat(),
                "current_results": current_state,
                "error": session_data.get("error")
            },
            message=f"Workflow status: {session_data['status']}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/events/results/{session_id}", response_model=EventResponse)
async def get_workflow_results(session_id: str):
    """Get complete workflow results"""
    try:
        session_data = validate_session(session_id)
        
        if session_data["status"] not in ["completed", "failed"]:
            return EventResponse(
                success=False,
                session_id=session_id,
                stage=session_data.get("stage", "unknown"),
                progress=session_data.get("progress", 0),
                message="Workflow not yet completed",
                data={"status": session_data["status"]}
            )
        
        result = session_data.get("workflow_result", {})
        
        return EventResponse(
            success=result.get("success", False),
            session_id=session_id,
            stage=session_data.get("stage", "completed"),
            progress=session_data.get("progress", 100),
            data=result,
            message="Workflow results retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/events/select", response_model=EventResponse) 
async def handle_user_selection(selection: UserSelection):
    """Handle user selections during workflow"""
    try:
        session_data = validate_session(selection.session_id)
        
        # Store user selection
        if "user_selections" not in session_data:
            session_data["user_selections"] = {}
        
        session_data["user_selections"][selection.selection_type] = {
            "selected_items": selection.selected_items,
            "feedback": selection.feedback,
            "revision_requests": selection.revision_requests,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update workflow state to continue processing
        session_data["status"] = "processing_selection"
        
        return EventResponse(
            success=True,
            session_id=selection.session_id,
            message=f"Selection for {selection.selection_type} recorded successfully",
            data={"selection_type": selection.selection_type}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling user selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/events/control", response_model=EventResponse)
async def control_workflow(control: WorkflowControl):
    """Control workflow execution (pause, resume, restart, cancel)"""
    try:
        session_data = validate_session(control.session_id)
        
        if control.action == "cancel":
            session_data.update({
                "status": "cancelled",
                "cancelled_at": datetime.now(),
                "stage": "cancelled"
            })
        elif control.action == "restart":
            # Reset session for restart
            original_input = session_data.get("workflow_input")
            if original_input:
                session_data.update({
                    "workflow_result": None,
                    "current_state": {},
                    "status": "active",
                    "stage": "initialized",
                    "progress": 0,
                    "user_selections": {}
                })
        elif control.action == "pause":
            session_data.update({
                "status": "paused",
                "paused_at": datetime.now()
            })
        elif control.action == "resume":
            if session_data.get("status") == "paused":
                session_data.update({
                    "status": "running",
                    "resumed_at": datetime.now()
                })
        
        return EventResponse(
            success=True,
            session_id=control.session_id,
            message=f"Workflow {control.action} executed successfully",
            data={"action": control.action, "reason": control.reason}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/events/export/{session_id}")
async def export_event_plan(session_id: str, format: str = "pdf"):
    """Export event plan in various formats"""
    try:
        session_data = validate_session(session_id)
        result = session_data.get("workflow_result", {})
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail="No completed event plan to export")
        
        event_plan = result.get("event_plan", result)
        
        if format.lower() == "pdf":
            # Generate PDF
            pdf_helper = PDFHelper()
            pdf_content = pdf_helper.generate_event_plan_pdf(event_plan)
            
            return StreamingResponse(
                io.BytesIO(pdf_content),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=event_plan_{session_id}.pdf"}
            )
            
        elif format.lower() == "ics":
            # Generate ICS calendar file
            ics_generator = ICSGenerator()
            ics_content = ics_generator.generate_event_ics(event_plan)
            
            return StreamingResponse(
                io.BytesIO(ics_content.encode()),
                media_type="text/calendar",
                headers={"Content-Disposition": f"attachment; filename=event_{session_id}.ics"}
            )
            
        elif format.lower() == "json":
            return JSONResponse(content=event_plan)
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting event plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sessions", response_model=List[Dict[str, Any]])
async def list_active_sessions():
    """List all active sessions (for debugging)"""
    try:
        sessions = []
        for session_id, data in active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "status": data["status"],
                "stage": data.get("stage", "unknown"),
                "progress": data.get("progress", 0),
                "created_at": data["created_at"].isoformat(),
                "has_result": "workflow_result" in data
            })
        
        return sessions
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        if session_id in active_sessions:
            del active_sessions[session_id]
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/v1/events/send_email", response_model=Dict[str, Any])
async def send_email_to_guests(payload: EmailSendRequest):
    """Send email invitations to guests"""
    try:
        session_data = validate_session(payload.session_id)
        result = session_data.get("workflow_result", {})

        if not result or not result.get("success"):
            raise HTTPException(status_code=400, detail="No valid event plan found to email")

        event_plan = result.get("event_plan", result)
        
        # Initialize email agent
        email_agent = EmailAgent()
        
        # Prepare email content
        email_body = payload.custom_message or event_plan.get("description", "You're invited to our event!")
        
        # Prepare attachments
        attachments = []
        
        if payload.attach_pdf:
            try:
                pdf_helper = PDFHelper()
                pdf_content = pdf_helper.generate_event_plan_pdf(event_plan)
                pdf_path = f"/tmp/{payload.session_id}_event_plan.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(pdf_content)
                attachments.append(pdf_path)
            except Exception as e:
                logger.warning(f"Failed to generate PDF attachment: {e}")

        if payload.attach_ics:
            try:
                ics_generator = ICSGenerator()
                ics_content = ics_generator.generate_event_ics(event_plan)
                ics_path = f"/tmp/{payload.session_id}_event.ics"
                with open(ics_path, "w") as f:
                    f.write(ics_content)
                attachments.append(ics_path)
            except Exception as e:
                logger.warning(f"Failed to generate ICS attachment: {e}")

        # Send email
        html_body = email_agent.create_html_email(
            event_name=event_plan.get("event_name", "Event"),
            content=email_body,
            event_details=event_plan
        )

        response = email_agent.send_email(
            sender_email=payload.sender_email,
            sender_password=payload.sender_password,
            recipient_emails=payload.recipients,
            subject=payload.subject,
            text_content=email_body,
            html_content=html_body,
            attachments=attachments
        )

        # Clean up temporary files
        for file_path in attachments:
            try:
                os.remove(file_path)
            except:
                pass

        return {
            "success": True,
            "message": "Emails sent successfully",
            "details": response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time workflow updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send periodic updates about workflow progress
            if session_id in active_sessions:
                session_data = active_sessions[session_id]
                
                update = {
                    "session_id": session_id,
                    "status": session_data["status"],
                    "progress": session_data.get("progress", 0),
                    "stage": session_data.get("stage", "unknown"),
                    "timestamp": datetime.now().isoformat(),
                    "has_results": "workflow_result" in session_data
                }
                
                await websocket.send_json(update)
                
                # If workflow is completed, send final results
                if session_data["status"] in ["completed", "failed", "error"]:
                    break
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")

# Additional utility endpoints
@app.get("/api/v1/events/stream/{session_id}")
async def stream_workflow_progress(session_id: str):
    """Stream workflow progress using Server-Sent Events"""
    
    def generate_progress_stream():
        while session_id in active_sessions:
            session_data = active_sessions[session_id]
            
            data = {
                "session_id": session_id,
                "status": session_data["status"],
                "progress": session_data.get("progress", 0),
                "stage": session_data.get("stage", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            
            if session_data["status"] in ["completed", "failed", "error", "cancelled"]:
                break
                
            # Wait before next update
            import time
            time.sleep(2)
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )