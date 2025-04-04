from pydantic import BaseModel, Field
from typing import List, Optional


class TeamInfo(BaseModel):
    """A class for holding information about an agent team.

    Attributes:
        name: The name of the team
        identifier: The identifier of the team
        agent_ids: List of agent IDs that are part of this team
        collaboration_name: Optional name for collaboration context
        service_names: List of service names available to this team
    """
    name: str
    identifier: str
    agent_ids: List[str] = Field(default_factory=list)
    collaboration_name: Optional[str] = None
    service_names: List[str] = Field(default_factory=list)