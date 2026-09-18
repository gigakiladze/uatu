from uatu.models.base import Document


class Project(Document):
    name: str
    description: str