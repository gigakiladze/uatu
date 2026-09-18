

from uatu.graphs.ingest.state import IngestState
from uatu.services import knowledge


def extract(state: IngestState) -> dict:   
    return {"items": knowledge.extract(state["raw_text"])}

def persist(state: IngestState) -> dict:
    return knowledge.ingest(state["items"], state["project_id"])