from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from uatu.graphs.index.node import list_files, persist, resolve, summarize_one
from uatu.graphs.index.state import IndexState


def _unchanged(state: IndexState):
    return END if state.get("skip") else "list_files"


def _dispatch(state: IndexState):
    if not state["todo"]:
        return "persist"
    return [
        Send(
            "summarize_one",
            {
                "entry": entry,
                "project_id": state["project_id"],
                "repo": state["repo"],
                "token": state["token"],
                "sha": state["sha"],
                "version": state["version"],
            },
        )
        for entry in state["todo"]
    ]


_builder = StateGraph(IndexState)
_builder.add_node("resolve", resolve)
_builder.add_node("list_files", list_files)
_builder.add_node("summarize_one", summarize_one)
_builder.add_node("persist", persist)

_builder.add_edge(START, "resolve")
_builder.add_conditional_edges("resolve", _unchanged, ["list_files", END])
_builder.add_conditional_edges("list_files", _dispatch, ["summarize_one", "persist"])
_builder.add_edge("summarize_one", "persist")
_builder.add_edge("persist", END)

graph = _builder.compile()