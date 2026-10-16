from langchain_core.messages import SystemMessage, AIMessage
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from typing import Literal
from config.settings import RUNNER_MODEL_BASE_URL, RUNNER_MODEL
from config.prompts import ORCHESTRATOR, ROUTER_PROMPT, CHITCHAT_REPLIES, OUT_OF_SCOPE_REPLIES
from schemas.state_schema import State
from schemas.route_schema import Route
import random


def handle_orchestrator_agent(state: State) -> Command[Literal["faq_agent", "reservation_agent", "__end__"]]:
    
    llm = init_chat_model(
        RUNNER_MODEL,
        model_provider="openai",
        base_url=RUNNER_MODEL_BASE_URL,
        api_key="no-api-key",
        temperature=0,
        max_tokens=1024,
    )

    router_llm = llm.with_structured_output(Route)

    route = router_llm.invoke([SystemMessage(content=ROUTER_PROMPT), *state["messages"][-6:]])
    pending = state.get("pending_agent")

    if pending and route.intent in ("chitchat", "out_of_scope"):
        return Command(goto=pending)
    
    if route.intent == "reservation":
        return Command(goto="reservation_agent")
    
    if route.intent == "faq":
        return Command(goto="faq_agent", update={"pending_agent": None})

    replies = CHITCHAT_REPLIES if route.intent == "chitchat" else OUT_OF_SCOPE_REPLIES
    return Command(
        goto="__end__",
        update={"messages": [AIMessage(content=random.choice(replies))], "pending_agent": None},
    )