from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, AIMessage
from langsmith import traceable
from config.settings import RUNNER_MODEL_BASE_URL, RUNNER_MODEL
from contextvars import ContextVar

TOOL_LOG: ContextVar[list | None] = ContextVar("tool_log", default=None)

@traceable
async def run_core(messages: str, tools: list = [], temperature: float = 0, max_iteration: int = 5):
    tool_map = {t.name: t for t in tools}
    MAX_CALLS_PER_TURN = 3
    MAX_TOTAL_CALLS = 4

    # Initialize LLM with the specified model and parameters
    llm = init_chat_model(
        RUNNER_MODEL,
        model_provider="openai",
        base_url=RUNNER_MODEL_BASE_URL,
        api_key="no-api-key",
        temperature=temperature,
        max_tokens=1024,
    )

    # Tool checking if tools are provided
    model = llm.bind_tools(tools) if tools else llm

    total_calls = 0
    seen = set()

    for _ in range(max_iteration):
        response = await model.ainvoke(messages)

        # If not tool is being called
        if not response.tool_calls:
            return response

        messages.append(response)

        for i, call in enumerate(response.tool_calls):
            key = (call["name"], str(call["args"]))

            if i >= MAX_CALLS_PER_TURN or total_calls >= MAX_TOTAL_CALLS or key in seen:
                messages.append(ToolMessage(
                    content="Skipped. Answer using the results you already have.",
                    tool_call_id=call["id"]
                ))
                continue

            seen.add(key)
            total_calls += 1

            tool = tool_map.get(call["name"])
            log = TOOL_LOG.get()

            if log is not None:
                log.append({"name": call["name"], "args": call["args"]})

            if tool is None:
                output = f"Error: Tool '{call["name"]}' not found."
            else:
                try:
                    output = await tool.ainvoke(call["args"])
                except Exception as e:
                    output = f"Error executing tool '{call["name"]}': {e}"

            messages.append(ToolMessage(
                content=str(output),
                tool_call_id=call["id"]
            ))

        if total_calls >= MAX_TOTAL_CALLS:
            return await llm.ainvoke(messages)

    return await llm.ainvoke(messages)