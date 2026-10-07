from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from schemas.state_schema import State
from agents.orchestrator_agent import handle_orchestrator_agent
from agents.faq_agent import handle_faq_agent
from agents.reservation_agent import handle_reservation_agent

# Initialize Graph
builder = StateGraph(State)

# Add all the nodes needed
builder.add_node("orchestrator_agent", handle_orchestrator_agent)
builder.add_node("faq_agent", handle_faq_agent)
builder.add_node("reservation_agent", handle_reservation_agent)

builder.add_edge(START, "orchestrator_agent")
builder.add_edge("faq_agent", END)
builder.add_edge("reservation_agent", END)

graph = builder.compile(checkpointer=MemorySaver())