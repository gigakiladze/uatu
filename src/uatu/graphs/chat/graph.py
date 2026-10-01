from langgraph.checkpoint.base import BaseCheckpointSaver
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

def build(checkpointer: BaseCheckpointSaver | None = None):
    """Compile for a host that owns its own persistence — our FastAPI, or a
    notebook. Pass MemorySaver for dev, MongoDBSaver later.
    """
    return _builder.compile(checkpointer=checkpointer)


# For langgraph dev and LangGraph API: NO checkpointer. The platform supplies
# one, and 0.15.1 refuses to load the graph if we bring our own.
graph = _builder.compile()