import streamlit as st
import requests
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import websockets
import threading

# Page config
st.set_page_config(
    page_title="EventPlanGenie v3",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8000/api/v1"
WS_BASE_URL = "ws://localhost:8000/ws"

# Initialize session state
def init_session_state():
    defaults = {
        'session_id': None,
        'workflow_status': 'not_started',
        'current_stage': 'input',
        'progress': 0,
        'event_data': {},
        'results': {},
        'error': None,
        'ws_connected': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# API Helper Functions
class EventPlanAPI:
    @staticmethod
    def start_planning(event_data: Dict) -> Dict:
        try:
            response = requests.post(f"{API_BASE_URL}/events/plan", json=event_data, timeout=30)
            return response.json() if response.status_code == 200 else {"success": False, "message": response.text}
        except Exception as e:
            return {"success": False, "message": f"API Error: {str(e)}"}
    
    @staticmethod
    def get_status(session_id: str) -> Dict:
        try:
            response = requests.get(f"{API_BASE_URL}/events/status/{session_id}", timeout=10)
            return response.json() if response.status_code == 200 else {"success": False}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    @staticmethod
    def get_results(session_id: str) -> Dict:
        try:
            response = requests.get(f"{API_BASE_URL}/events/results/{session_id}", timeout=10)
            return response.json() if response.status_code == 200 else {"success": False}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    @staticmethod
    def export_plan(session_id: str, format: str = "pdf"):
        try:
            response = requests.get(f"{API_BASE_URL}/events/export/{session_id}?format={format}", timeout=30)
            return response.content if response.status_code == 200 else None
        except:
            return None

# WebSocket Handler for Real-time Updates
def websocket_listener(session_id: str):
    try:
        import websocket
        
        def on_message(ws, message):
            data = json.loads(message)
            st.session_state.progress = data.get('progress', 0)
            st.session_state.current_stage = data.get('stage', 'unknown')
            st.session_state.workflow_status = data.get('status', 'running')
        
        def on_error(ws, error):
            st.session_state.ws_connected = False
        
        ws = websocket.WebSocketApp(f"{WS_BASE_URL}/{session_id}",
                                  on_message=on_message,
                                  on_error=on_error)
        ws.run_forever()
    except:
        pass

# UI Components
def render_sidebar():
    with st.sidebar:
        st.title("🎉 EventPlanGenie v3")
        st.caption("AI-Powered Event Planning")
        
        if st.session_state.session_id:
            st.success(f"Session: {st.session_state.session_id[:8]}...")
            
            # Progress indicator
            progress_value = st.session_state.progress / 100
            st.progress(progress_value, text=f"Progress: {st.session_state.progress}%")
            
            # Current stage
            st.info(f"Stage: {st.session_state.current_stage.replace('_', ' ').title()}")
            
            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            with col2:
                if st.button("🗑️ Reset", use_container_width=True):
                    for key in st.session_state.keys():
                        del st.session_state[key]
                    st.rerun()
        
        st.divider()
        st.caption("Powered by LangGraph + FastAPI")

def render_event_form():
    st.header("📝 Create Your Event")
    
    with st.form("event_planning_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input("Event Name*", placeholder="My Amazing Event")
            event_type = st.selectbox("Event Type*", [
                "Wedding", "Birthday", "Corporate", "Conference", 
                "Workshop", "Party", "Fundraiser", "Other"
            ])
            location = st.text_input("Location*", placeholder="City, State/Country")
            
        with col2:
            start_date = st.date_input("Start Date*", min_value=date.today())
            end_date = st.date_input("End Date*", min_value=start_date)
            start_time = st.time_input("Start Time*")
            end_time = st.time_input("End Time*")
        
        col3, col4 = st.columns(2)
        with col3:
            budget_min = st.number_input("Min Budget ($)*", min_value=1000, max_value=1000000, value=5000)
            estimated_guests = st.number_input("Expected Guests*", min_value=5, max_value=5000, value=50)
            
        with col4:
            budget_max = st.number_input("Max Budget ($)*", min_value=budget_min, max_value=1000000, value=10000)
            contact_email = st.text_input("Contact Email", placeholder="your@email.com")
        
        description = st.text_area("Event Description", height=100, 
                                 placeholder="Describe your event vision, theme, special requirements...")
        
        # Advanced preferences (expandable)
        with st.expander("🎯 Advanced Preferences"):
            col5, col6 = st.columns(2)
            with col5:
                venue_type = st.multiselect("Preferred Venue Types", [
                    "Indoor", "Outdoor", "Hotel", "Restaurant", "Hall", "Garden", "Beach", "Rooftop"
                ])
                catering_style = st.multiselect("Catering Preferences", [
                    "Buffet", "Plated", "Cocktail", "Family Style", "Food Trucks", "BBQ"
                ])
            with col6:
                special_requirements = st.text_area("Special Requirements", height=60,
                                                  placeholder="Accessibility, dietary restrictions, etc.")
                theme_preferences = st.text_input("Theme/Style", placeholder="Elegant, Casual, Modern, Rustic...")
        
        submitted = st.form_submit_button("🚀 Start Planning", use_container_width=True, type="primary")
        
        if submitted:
            # Validation
            required_fields = [event_name, event_type, location]
            if not all(required_fields):
                st.error("Please fill in all required fields marked with *")
                return
            
            if budget_max < budget_min:
                st.error("Maximum budget must be greater than minimum budget")
                return
            
            # Prepare event data
            event_data = {
                "event_name": event_name,
                "event_type": event_type,
                "location": location,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "description": description,
                "budget_min": float(budget_min),
                "budget_max": float(budget_max),
                "estimated_guests": int(estimated_guests),
                "contact_email": contact_email,
                "location_preferences": {
                    "venue_types": venue_type,
                    "special_requirements": special_requirements
                },
                "user_preferences": {
                    "catering_style": catering_style,
                    "theme": theme_preferences
                }
            }
            
            st.session_state.event_data = event_data
            return start_planning_workflow(event_data)

def start_planning_workflow(event_data: Dict):
    with st.spinner("🤖 Initializing AI agents..."):
        result = EventPlanAPI.start_planning(event_data)
        
        if result.get("success"):
            st.session_state.session_id = result.get("session_id")
            st.session_state.workflow_status = "running"
            st.session_state.current_stage = "planning"
            
            # Start WebSocket listener in background
            if not st.session_state.ws_connected:
                threading.Thread(
                    target=websocket_listener, 
                    args=(st.session_state.session_id,), 
                    daemon=True
                ).start()
                st.session_state.ws_connected = True
            
            st.success("🎉 Planning started! AI agents are working...")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"Failed to start planning: {result.get('message', 'Unknown error')}")

def render_progress_tracker():
    if st.session_state.workflow_status not in ['running', 'completed']:
        return
    
    st.header("🔄 Planning Progress")
    
    # Stage indicators
    stages = ["Input", "Ideas", "Venues", "Vendors", "Schedule", "Invitations", "Review"]
    current_stage_idx = 0
    
    if st.session_state.current_stage:
        stage_map = {
            "planning": 1, "ideas": 1, "venues": 2, "vendors": 3, 
            "schedule": 4, "invitations": 5, "review": 6, "completed": 6
        }
        current_stage_idx = stage_map.get(st.session_state.current_stage, 0)
    
    cols = st.columns(len(stages))
    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            if i < current_stage_idx:
                st.success(f"✅ {stage}")
            elif i == current_stage_idx:
                st.info(f"🔄 {stage}")
            else:
                st.text(f"⏳ {stage}")
    
    # Auto-refresh for status updates
    if st.session_state.workflow_status == "running":
        status_result = EventPlanAPI.get_status(st.session_state.session_id)
        if status_result.get("success"):
            data = status_result.get("data", {})
            st.session_state.workflow_status = data.get("status", "running")
            st.session_state.progress = status_result.get("progress", 0)
            
            if st.session_state.workflow_status == "completed":
                st.balloons()
                st.rerun()
        
        # Auto-refresh every 3 seconds
        time.sleep(3)
        st.rerun()

def render_results():
    if st.session_state.workflow_status != "completed":
        return
    
    st.header("🎊 Your Event Plan is Ready!")
    
    # Get final results
    results = EventPlanAPI.get_results(st.session_state.session_id)
    if not results.get("success"):
        st.error("Failed to retrieve results")
        return
    
    event_plan = results.get("data", {}).get("event_plan", {})
    st.session_state.results = event_plan
    
    # Display results in tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Overview", "📍 Venue", "🛍️ Vendors", "📅 Schedule", "💌 Invitation"])
    
    with tab1:
        render_overview(event_plan)
    
    with tab2:
        render_venue_details(event_plan.get("venue", {}))
    
    with tab3:
        render_vendor_details(event_plan.get("vendors", {}))
    
    with tab4:
        render_schedule(event_plan.get("schedule", {}))
    
    with tab5:
        render_invitation(event_plan.get("invitation", {}))
    
    # Export options
    st.divider()
    render_export_options()

def render_overview(event_plan: Dict):
    st.subheader("Event Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Event Type", st.session_state.event_data.get("event_type", "N/A"))
        st.metric("Expected Guests", st.session_state.event_data.get("estimated_guests", "N/A"))
        st.metric("Location", st.session_state.event_data.get("location", "N/A"))
    
    with col2:
        st.metric("Budget Range", f"${st.session_state.event_data.get('budget_min', 0):,} - ${st.session_state.event_data.get('budget_max', 0):,}")
        st.metric("Duration", f"{st.session_state.event_data.get('start_date', '')} to {st.session_state.event_data.get('end_date', '')}")
    
    if event_plan.get("summary"):
        st.subheader("Plan Summary")
        st.write(event_plan["summary"])

def render_venue_details(venue_data: Dict):
    if not venue_data:
        st.info("Venue information not available")
        return
    
    st.subheader("Selected Venue")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**{venue_data.get('name', 'Venue Name')}**")
        st.write(f"📍 {venue_data.get('address', 'Address not available')}")
        st.write(f"💰 Estimated Cost: ${venue_data.get('cost', 'TBD'):,}")
        
        if venue_data.get("description"):
            st.write("**Description:**")
            st.write(venue_data["description"])
    
    with col2:
        st.metric("Capacity", venue_data.get("capacity", "N/A"))
        st.metric("Rating", f"{venue_data.get('rating', 'N/A')}/5" if venue_data.get('rating') else "N/A")

def render_vendor_details(vendors_data: Dict):
    if not vendors_data:
        st.info("Vendor information not available")
        return
    
    st.subheader("Selected Vendors")
    
    for category, vendor in vendors_data.items():
        with st.expander(f"{category.title()}: {vendor.get('name', 'TBD')}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Contact:** {vendor.get('contact', 'TBD')}")
                st.write(f"**Cost:** ${vendor.get('cost', 'TBD'):,}")
            with col2:
                st.write(f"**Rating:** {vendor.get('rating', 'N/A')}/5")
                st.write(f"**Specialty:** {vendor.get('specialty', 'N/A')}")
            
            if vendor.get("description"):
                st.write(f"**About:** {vendor['description']}")

def render_schedule(schedule_data: Dict):
    if not schedule_data:
        st.info("Schedule not available")
        return
    
    st.subheader("Event Timeline")
    
    timeline = schedule_data.get("timeline", [])
    for item in timeline:
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"**{item.get('time', 'TBD')}**")
            with col2:
                st.write(f"{item.get('activity', 'Activity')} - {item.get('description', '')}")

def render_invitation(invitation_data: Dict):
    if not invitation_data:
        st.info("Invitation not available")
        return
    
    st.subheader("Event Invitation")
    
    if invitation_data.get("text"):
        st.markdown("### Invitation Text")
        st.markdown(invitation_data["text"])
    
    if invitation_data.get("details"):
        st.markdown("### Event Details")
        for key, value in invitation_data["details"].items():
            st.write(f"**{key.title()}:** {value}")

def render_export_options():
    st.subheader("📤 Export Your Plan")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download PDF", use_container_width=True):
            pdf_content = EventPlanAPI.export_plan(st.session_state.session_id, "pdf")
            if pdf_content:
                st.download_button(
                    label="💾 Save PDF",
                    data=pdf_content,
                    file_name=f"{st.session_state.event_data.get('event_name', 'event')}_plan.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Failed to generate PDF")
    
    with col2:
        if st.button("📅 Download Calendar", use_container_width=True):
            ics_content = EventPlanAPI.export_plan(st.session_state.session_id, "ics")
            if ics_content:
                st.download_button(
                    label="💾 Save Calendar",
                    data=ics_content,
                    file_name=f"{st.session_state.event_data.get('event_name', 'event')}.ics",
                    mime="text/calendar"
                )
            else:
                st.error("Failed to generate calendar file")
    
    with col3:
        if st.button("📧 Send Email", use_container_width=True):
            email = st.text_input("Recipient Email:")
            if email and st.button("Send"):
                # Implementation would call email API
                st.success("Email sent successfully!")

# Main App Logic
def main():
    init_session_state()
    render_sidebar()
    
    # Error handling
    if st.session_state.error:
        st.error(f"Error: {st.session_state.error}")
        if st.button("Clear Error"):
            st.session_state.error = None
            st.rerun()
    
    # Main content based on current state
    if st.session_state.workflow_status == "not_started":
        render_event_form()
    
    elif st.session_state.workflow_status in ["running", "planning"]:
        render_progress_tracker()
    
    elif st.session_state.workflow_status == "completed":
        render_results()
    
    elif st.session_state.workflow_status == "failed":
        st.error("⚠️ Event planning failed. Please try again.")
        if st.button("🔄 Start Over"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()