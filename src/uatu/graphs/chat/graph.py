from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from uatu.graphs.chat.node import agent, tools
from uatu.graphs.chat.state import ChatState


def _next(state: ChatState):
    return "tools" if state["messages"][-1].tool_calls else END


_builder = StateGraph(ChatState)
_builder.add_node("agent", agent)
_builder.add_node("tools", tools)

_builder.add_edge(START, "agent")
_builder.add_conditional_edges("agent", _next, ["tools", END])
_builder.add_edge("tools", "agent")

graph = _builder.compile(checkpointer=MemorySaver())