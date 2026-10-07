from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from schemas.state_schema import State
from agents.orchestrator_agent import handle_orchestrator_agent
from agents.faq_agent import handle_faq_agent
from agents.reservation_agent import handle_reservation_agent
from functools import lru_cache

def build_graph(checkpointer=None):
    # Initialize Graph
    builder = StateGraph(State)

    # Add all the nodes needed
    builder.add_node("orchestrator_agent", handle_orchestrator_agent)
    builder.add_node("faq_agent", handle_faq_agent)
    builder.add_node("reservation_agent", handle_reservation_agent)

    # Assign the flow 
    builder.add_edge(START, "orchestrator_agent")
    builder.add_edge("faq_agent", END)
    builder.add_edge("reservation_agent", END)

    # Compile the graph
    return builder.compile(checkpointer=checkpointer)
   
@lru_cache(maxsize=1)
def get_graph():
    return build_graph(checkpointer=MemorySaver())

async def run_graph(message: str, session_id: str):
    result = await get_graph().ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": session_id}}
    )

    return {
        "message": result["messages"][-1].content,
        "session_id": session_id
    }