from uatu.libs.config import settings
from uatu.libs.repository import MongoRepository
from uatu.models import Project

collection = "projects"

project_store = MongoRepository(collection, Project)

def ensure_indexes() -> None:
    project_store.col.create_index([("name", 1)], unique=True)


def getByFilter(filter: dict) -> list[Project]:
    return list(project_store.find(filter))

def create(project: Project) -> Project:
    return project_store.insert(project)


# get Project with pagination
def getProjects(page: int = 1, page_size: int = 10) -> list[Project]:
    skip = (page - 1) * page_size
    return list(project_store.find({}, skip=skip, limit=page_size))