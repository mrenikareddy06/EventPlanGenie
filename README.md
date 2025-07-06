# EventPlanGenie
An Agentic AI-powered Multi-Agent Event Planning System using LangGraph, Streamlit &amp; FastAPI

> Built with LangGraph + LangChain | Modular AI Agents | Local-First Architecture

---

## Overview

**EventPlanGenie** is a smart event planning assistant powered by multiple collaborating AI agents. It uses local LLMs and a modular architecture to automate creative and logistical planning task.

> Plan smarter, faster, and locally — no cloud dependencies.

---

## Features

- Fully local execution using LLMs via Ollama (`phi3`)  
- Modular multi-agent system (Idea, Vendor, Scheduler, Invitation, Reviewer)  
- Markdown and PDF export  
- Email-ready event invitations  
- Agent coordination via LangGraph protocol  
- MCP (Model-Context-Protocol) design pattern

---

## Tech Stack

| Layer         | Tech Used                      |
|---------------|--------------------------------|
| Frontend      | `Streamlit`                    |
| Backend       | `FastAPI`, `LangGraph`, `LangChain` |
| LLMs          | `phi3` via `Ollama`            |
| Export        | `markdown`, `reportlab`        |
| Emailing      | `smtplib`, `email`             |

---

## Project Structure

```bash
eventplangenie/
├── agents/                  # All AI agents (Idea, Vendor, Scheduler, etc.)
│   ├── base_agent.py
│   ├── idea_agent.py
│   ├── vendor_agent.py
│   ├── scheduler_agent.py
│   ├── invitation_agent.py
│   ├── reviewer_agent.py
│   └── email_agent.py
│
├── coordinator/            # LangGraph protocol graph (MCP)
│   └── graph.py
│
├── backend/                # FastAPI backend logic
│   └── main.py
│
├── frontend/               # Streamlit user interface
│   ├── streamlit_app.py
│   └── streamlit_app2.py
│
├── utils/                  # Helper utilities
│   ├── markdown_formatter.py
│   ├── pdf_helper.py
│   └── ics_generator.py    # (optional – remove if not used)
│
├── .env.example            #  Sample environment configuration
├── requirements.txt        #  Python dependencies
├── .gitignore              #  Git ignore rules
└── README.md               #  Project documentation
```
---

## Agent Roles 

| Agent            | Role                                                                 |
|------------------|----------------------------------------------------------------------|
| `IdeaAgent`      | Suggests creative event ideas                                         |
| `VendorAgent`    | Finds vendors based on event type/location                           |
| `SchedulerAgent` | Plans the timeline and event schedule                                |
| `InvitationAgent`| Generates a well-written invite (Markdown + PDF)                     |
| `ReviewerAgent`  | Reviews final output and suggests improvements                       |

All agents interact in LangGraph, forming a real-time decision flow.

---

##  How to Run

### 1. Clone and Setup

```bash
git clone https://github.com/mrenikareddy06/EventPlanGenie.git
cd EventPlanGenie
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
Update with your email config (if using email invites).
```

### 3. Start Backend
```bash
uvicorn backend.main:app --reload
```

### 4. Launch Frontend
```bash
streamlit run frontend/streamlit_app.py
```

## Output Formats
- PDF: Downloadable summary
- Email: Send invitation directly

## Architecture (Visualized)

![image](https://github.com/user-attachments/assets/5b9fe3e5-8e28-44d5-bfc4-b722afa9d9aa)
# EventPlanGenie-v3
