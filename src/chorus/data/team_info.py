from pydantic import BaseModel, Field
from typing import List, Optional


class TeamInfo(BaseModel):
    """A class for holding information about an agent team.

    Attributes:
        name: The name of the team
        agent_ids: List of agent IDs that are part of this team
        collaboration_name: Optional name for collaboration context
        service_names: List of service names available to this team
    """
    name: str
    agent_ids: Optional[List[str]] = Field(default_factory=list)
    collaboration_name: Optional[str] = None
    service_names: Optional[List[str]] = Field(default_factory=list)

    def get_identifier(self) -> str:
        """Gets a unique identifier string for this team.

        Returns:
            A string identifier in the format "team:{name}"
        """
        return f"team:{self.name}"
