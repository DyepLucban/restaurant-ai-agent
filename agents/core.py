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

    # Initialize LLM with the specified model and parameters
    llm = init_chat_model(
        RUNNER_MODEL, # your model name, exactly as Docker lists it
        model_provider="openai", # use the OpenAI-compatible client
        base_url=RUNNER_MODEL_BASE_URL,
        api_key="no-api-key", # required by the client, ignored by Docker
        temperature=temperature,
        max_tokens=1024,
    )

    # Tool checking if tools are provided
    model = llm.bind_tools(tools) if tools else llm

    for _ in range(max_iteration):
        response = await model.ainvoke(messages)

        # Check if tool is needed
        if not response.tool_calls:
            # Return the response if no tool calls are made
            print(f"NO TOOL BEING CALLED")
            return response

        if len(response.tool_calls) > 3:
            return AIMessage(content="Sorry, I had trouble checking that. Could you rephrase?")

        messages.append(response)

        for call in response.tool_calls:
            tool = tool_map.get(call["name"])
            print(f"TOOL CALLED: {tool}")

            log = TOOL_LOG.get()
            if log is not None:
                log.append({"name": call["name"], "args": call["args"]})

            # Check if tool does not exist
            if tool is None:
                print(f"Error: Tool '{call['name']}' not found.")
                output = f"Error: Tool '{call['name']}' not found."
            else:
                try:
                    output = await tool.ainvoke(call["args"])
                except Exception as e:
                    print(f"Error executing tool '{call['name']}': {e}")
                    output = f"Error executing tool '{call['name']}': {e}"
            messages.append(ToolMessage(content=str(output),tool_call_id=call["id"]))

    fallback = AIMessage(content="Sorry, I couldn't complete that request.")
    messages.append(fallback)

    return fallback