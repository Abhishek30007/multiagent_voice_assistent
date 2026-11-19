from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes.supervisor import supervisor_node
from app.agent.nodes.gmail_agent import gmail_agent_node
from app.agent.nodes.calendar_agent import calendar_agent_node
from app.agent.nodes.evidence_validator import evidence_validation_node
from app.agent.nodes.safety_agent import safety_agent_node
from app.agent.nodes.response_agent import response_agent_node


def route_supervisor(state: AgentState) -> str:
    """Conditional routing based on supervisor node output."""
    route = state.get("route", "both")
    if route == "safety_block":
        return "safety_agent"
    elif route == "direct":
        return "evidence_validator"
    elif route == "gmail":
        return "gmail_agent"
    elif route == "calendar":
        return "calendar_agent"
    else:
        # "both" -> visit calendar_agent first, then gmail_agent
        return "calendar_agent"


def build_multiagent_graph():
    """Construct and compile the LangGraph workflow for the Personal AI Twin."""
    workflow = StateGraph(AgentState)

    # 1. Add all agent nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("gmail_agent", gmail_agent_node)
    workflow.add_node("calendar_agent", calendar_agent_node)
    workflow.add_node("evidence_validator", evidence_validation_node)
    workflow.add_node("safety_agent", safety_agent_node)
    workflow.add_node("response_agent", response_agent_node)

    # 2. Add entrypoint
    workflow.add_edge(START, "supervisor")

    # 3. Add conditional routing from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "safety_agent": "safety_agent",
            "evidence_validator": "evidence_validator",
            "gmail_agent": "gmail_agent",
            "calendar_agent": "calendar_agent",
        },
    )

    # 4. Sequential transitions
    # If starting at calendar_agent and needs_gmail is True, transition to gmail_agent
    def route_after_calendar(state: AgentState) -> str:
        if state.get("needs_gmail", False) and state.get("route") == "both":
            return "gmail_agent"
        return "evidence_validator"

    workflow.add_conditional_edges(
        "calendar_agent",
        route_after_calendar,
        {
            "gmail_agent": "gmail_agent",
            "evidence_validator": "evidence_validator",
        },
    )

    workflow.add_edge("gmail_agent", "evidence_validator")
    workflow.add_edge("evidence_validator", "safety_agent")
    workflow.add_edge("safety_agent", "response_agent")
    workflow.add_edge("response_agent", END)

    return workflow.compile()


# Compiled singleton instance
personal_ai_graph = build_multiagent_graph()
