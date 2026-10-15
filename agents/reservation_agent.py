from langchain_core.messages import SystemMessage, AIMessage
from tools.reservation_tool import search_available_tables, book_table
from agents.core import run_core
from config.prompts import RESERVATION_PROMPT
from schemas.state_schema import State

async def handle_reservation_agent(state: State):
    # Agent Tools
    tools = [
        search_available_tables,
        book_table
    ]

    # Build message
    messages = [
        SystemMessage(content=RESERVATION_PROMPT),
        *state["messages"][-6:]
    ]

    response = (await run_core(messages, tools, 0.4)).content

    return {
        "messages": [AIMessage(content=response, name="reservation_agent")],
        "pending_agent": "reservation_agent" if response.strip().endswith("?") else None,
    }
