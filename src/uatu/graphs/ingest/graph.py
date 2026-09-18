from langgraph.graph import END, START, StateGraph

from uatu.graphs.ingest.node import extract, persist
from uatu.graphs.ingest.state import IngestState


_builder = StateGraph(IngestState)
_builder.add_node("extract", extract)
_builder.add_node("persist", persist)
_builder.add_edge(START, "extract")
_builder.add_edge("extract", "persist")
_builder.add_edge("persist", END)
graph = _builder.compile()