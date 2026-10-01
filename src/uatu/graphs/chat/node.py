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
def _llm() -> ChatOllama:
    
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_url,
        temperature=0,
    )


def agent(state: ChatState, config: RunnableConfig) -> dict:
    prompt = load("chat")
    llm = _llm().bind_tools(TOOLS)

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