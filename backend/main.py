from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from coordinator.graph import execute_graph, execute_final_plan
from agents.email_agent import send_email

app = FastAPI(
    title="EventPlanGenie API",
    description="Multi-Agent Event Planning Backend using LangGraph",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EventRequest(BaseModel):
    event_name: str
    event_type: str
    location: str
    date: str
    description: str

class FinalPlanRequest(EventRequest):
    selected_idea: str
    selected_venue: str
    selected_vendor: str

class EmailRequest(FinalPlanRequest):
    recipient_email: str

@app.post("/generate")
async def generate(req: EventRequest):
    """
    Step 1: Generate initial options using IdeaAgent, LocationAgent, and VendorAgent.
    Returns: list of ideas, venues, and vendor bundles.
    """
    return await execute_graph({
        "event_name": req.event_name,
        "event_type": req.event_type,
        "location": req.location,
        "date": req.date,
        "description": req.description
    })


@app.post("/generate_final_plan")
async def generate_final_plan(req: FinalPlanRequest):
    """
    Step 2: Finalize the event plan with selected options.
    Returns: Structured event plan with schedule, invitation, and review.
    """
    return await execute_final_plan({
        "event_name": req.event_name,
        "event_type": req.event_type,
        "location": req.location,
        "date": req.date,
        "description": req.description,
        "selected_idea": req.selected_idea,
        "selected_venue": req.selected_venue,
        "selected_vendor": req.selected_vendor
    })


@app.post("/send_email")
async def send_event_email(req: EmailRequest):
    """
    Optional: Deliver finalized plan via email to the user.
    """
    final_result = await execute_final_plan({
        "event_name": req.event_name,
        "event_type": req.event_type,
        "location": req.location,
        "date": req.date,
        "description": req.description,
        "selected_idea": req.selected_idea,
        "selected_venue": req.selected_venue,
        "selected_vendor": req.selected_vendor
    })

    subject = f"📅 Your Event Plan: {req.event_name} on {req.date}"
    html = final_result.get("final_output", "No plan generated.")
    email_response = send_email(req.recipient_email, subject, html)
    return email_response
