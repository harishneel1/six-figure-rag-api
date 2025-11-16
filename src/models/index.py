from pydantic import BaseModel, Field
from typing import Optional


class ProjectCreate(BaseModel):
    name: str = Field(..., description="The name of the project")
    description: Optional[str] = Field(None, description="Project description")
