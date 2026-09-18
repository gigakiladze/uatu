from contextlib import asynccontextmanager

from fastapi import FastAPI

from uatu.api.controllers import investigate, knowledge, project
from uatu.libs import db_service, qdrant_service
from uatu.libs.embedder import get_model
from uatu.store import knowledge as knowledge_store
from uatu.api.controllers import repo
from uatu.store import repo as repo_store
from uatu.store import code_file as code_file_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_model()                          
    knowledge_store.ensure_indexes()     
    knowledge_store.ensure_collection()  
    yield


app = FastAPI(title="uatu", version="0.1.0", lifespan=lifespan)

app.include_router(knowledge.router)
app.include_router(repo.router)
app.include_router(investigate.router)
app.include_router(project.router)
repo_store.ensure_indexes()
code_file_store.ensure_indexes()
code_file_store.ensure_collection()


@app.get("/health")
def health() -> dict:
    return {"mongo": db_service.ping(), "qdrant": qdrant_service.ping()}