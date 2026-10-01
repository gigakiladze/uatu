from functools import cache

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama

from uatu.libs.config import settings
from uatu.graphs.chat.state import ChatState
from uatu.graphs.chat.tools import TOOLS
from uatu.prompts import load

BY_NAME = {t.name: t for t in TOOLS}


@cache
def _llm(model: str, temperature: float) -> ChatOllama:
    """Cached per (model, temperature).

    Keyed on the arguments rather than nothing, so changing the model in
    chat.prompty hands back a new client instead of reusing the old one.
    Rebuilding per request would reopen the HTTP pool every turn.
    """
    return ChatOllama(
        model=model,
        base_url=settings.ollama_url,
        temperature=temperature,
    )


def agent(state: ChatState, config: RunnableConfig) -> dict:
    """Decide: answer, or call tools.

    The model comes from the prompty's `model:` block, not from
    settings.ollama_model. The agent needs a model trained for tool calling,
    while the deterministic chains want a code model — that choice belongs
    next to the prompt it is made for.
    """
    prompt = load("chat")
    spec = prompt.model

    llm = _llm(
        spec.get("name", settings.ollama_model),
        spec.get("parameters", {}).get("temperature", 0),
    ).bind_tools(TOOLS)

    messages = [SystemMessage(content=prompt.system)] + state["messages"]
    return {"messages": [llm.invoke(messages, config=config)]}


def tools(state: ChatState, config: RunnableConfig) -> dict:
    last = state["messages"][-1]
    out = []

    for call in last.tool_calls:
        tool = BY_NAME.get(call["name"])
        if tool is None:
            # Hallucinated tool name. Text, not an exception — the model reads
            # this and picks a real one next turn.
            result = f"No tool named {call['name']!r}. Available: {', '.join(BY_NAME)}"
        else:
            try:
                # config carries project_id. Drop it and every tool raises.
                result = tool.invoke(call["args"], config=config)
            except Exception as exc:
                result = f"{call['name']} failed: {exc}"

        # tool_call_id must match, or the next request is malformed.
        out.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

    return {"messages": out}