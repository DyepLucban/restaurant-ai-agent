from langchain_core.messages import SystemMessage, AIMessage
from agents.core import run_core
from config.prompts import FAQ_PROMPT
from schemas.state_schema import State
from tools.faq_tool import search_menu_docs

async def handle_faq_agent(state: State):
    # Agent Tools
    tools = [search_menu_docs]

    # Build message
    messages = [
        SystemMessage(content=FAQ_PROMPT),
        *state["messages"][-6:]
    ]

    response = (await run_core(messages, tools)).content

    return {"messages": [AIMessage(content=response)]}
    