from typing import TypedDict

from uatu.models import  KnowledgeItem

class IngestState(TypedDict, total=False):
    project_id: str              
    raw_text: str                
    items: list[KnowledgeItem]   
    saved: int                   
    indexed: int                 
