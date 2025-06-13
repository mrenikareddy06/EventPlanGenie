from langgraph.graph import StateGraph, END
from typing import Dict, Any

from agents.idea_agent import generate_ideas
from agents.location_agent import suggest_venues
from agents.vendor_agent import get_vendor_bundles
from agents.scheduler_agent import create_schedule
from agents.invitation_agent import generate_invitation
from agents.reviewer_agent import review_plan

schema = {
    "event_name": str,
    "event_type": str,
    "location": str,
    "date": str,
    "description": str,
    "ideas": list,
    "venues": list,
    "vendors": list
}

def parse_options(text: str) -> list:
    """
    Parse LLM output text into a clean list of options.
    Assumes options are on separate lines, possibly numbered or bulleted.
    """
    options = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        while line and (line[0].isdigit() or line[0] in "-•. "):
            line = line[1:].strip()
        if line:
            options.append(line)
    return options


def idea_step(state: Dict[str, Any]) -> Dict[str, Any]:
    print("🧠 Running IdeaAgent...")
    idea_output = generate_ideas(state)
    ideas = parse_options(idea_output)
    return {**state, "ideas": ideas}

def venue_step(state: Dict[str, Any]) -> Dict[str, Any]:
    print("📍 Running LocationAgent...")
    venue_output = suggest_venues(state)
    venues = parse_options(venue_output)
    return {**state, "venues": venues}

def vendor_step(state: Dict[str, Any]) -> Dict[str, Any]:
    print("🛍️ Running VendorAgent...")
    vendor_output = get_vendor_bundles(state)
    vendors = parse_options(vendor_output)
    return {**state, "vendors": vendors}


def build_generation_graph():
    builder = StateGraph(schema)  

    builder.add_node("idea", idea_step)
    builder.add_node("venue", venue_step)
    builder.add_node("vendor", vendor_step)

    builder.set_entry_point("idea")
    builder.add_edge("idea", "venue")
    builder.add_edge("venue", "vendor")
    builder.add_edge("vendor", END)

    return builder.compile()


generation_graph = build_generation_graph()

async def execute_graph(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the agentic planning pipeline:
    Step 1: IdeaAgent → LocationAgent → VendorAgent
    Returns the parsed options to Streamlit UI.
    """
    result = generation_graph.invoke(inputs)
    return {
        "ideas": result.get("ideas", []),
        "venues": result.get("venues", []),
        "vendors": result.get("vendors", [])
    }


async def execute_final_plan(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs should include:
    event_name, event_type, location, date, description,
    selected_idea, selected_venue, selected_vendor
    """
    print("🧾 Generating Final Plan...")

    schedule = create_schedule(inputs)
    invitation = generate_invitation(inputs)

    intro = f"""
## 📋 Event Overview

- **Event Name**: {inputs['event_name']}
- **Type**: {inputs['event_type']}
- **Location**: {inputs['location']}
- **Date**: {inputs['date']}
- **Description**: {inputs['description']}

### 🎨 Selected Idea:
{inputs['selected_idea']}

### 📍 Selected Venue:
{inputs['selected_venue']}

### 🛍️ Selected Vendor Package:
{inputs['selected_vendor']}

### ⏰ Schedule:
{schedule}

### 💌 Invitation:
{invitation}
"""

    final_output = review_plan({"full_plan": intro})
    return {"final_output": final_output}
