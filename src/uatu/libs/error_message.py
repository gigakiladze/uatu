from enum import Enum

class ErrorMessage(str, Enum):
    PROJECT_ALREADY_EXISTS = "Project with this name already exists.",
    PROJECT_NOT_FOUND = "Project not found.",