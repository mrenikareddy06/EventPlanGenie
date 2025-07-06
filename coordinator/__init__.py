
"""
EventPlanGenie Coordinator Package
The brain of the multi-agent event planning system

This package contains:
- graph.py: LangGraph orchestration (Protocol layer)  
- state_schema.py: Shared state definitions (Context layer)
- runner.py: Test runner and debugger
- config.py: Central configuration
"""

from .graph import EventPlanningGraph, create_event_planning_graph
from .state_schema import EventPlanState, EventType, AgentType
from .runner import EventPlanRunner
from .config import (
    DEFAULT_MODEL,
    OLLAMA_BASE_URL, 
    ENABLE_STREAMING,
    AGENT_CONFIGS
)

__version__ = "3.0.0"
__author__ = "EventPlanGenie Team"

# Main exports for easy importing
__all__ = [
    # Core classes
    "EventPlanningGraph",
    "EventPlanRunner", 
    "EventPlanState",
    
    # Factory functions
    "create_event_planning_graph",
    
    # Enums and types
    "EventType",
    "AgentType",
    
    # Configuration
    "DEFAULT_MODEL",
    "OLLAMA_BASE_URL",
    "ENABLE_STREAMING", 
    "AGENT_CONFIGS"
]

# Package metadata
__package_info__ = {
    "name": "eventplangenie-coordinator",
    "description": "Multi-agent event planning orchestration system",
    "keywords": ["ai", "agents", "event-planning", "langgraph", "mcp"],
    "dependencies": [
        "langgraph>=0.0.40",
        "langchain>=0.1.0",
        "langchain-ollama>=0.1.0"
    ]
}