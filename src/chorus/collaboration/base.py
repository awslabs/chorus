from typing import TYPE_CHECKING, List, Dict, Optional
from pydantic import BaseModel, ValidationError
from pydantic.tools import parse_obj_as
from chorus.config import Registrable
from abc import abstractmethod, ABCMeta

from chorus.data.dialog import Message
from chorus.data.team_info import TeamInfo

if TYPE_CHECKING:
    from chorus.data.context import TeamContext
    from chorus.data.state import TeamState
    from chorus.teams.services.base import TeamService


class TaskInfo(BaseModel):
    """Information about a queued task."""

    task_id: Optional[str] = None
    content: Optional[str] = None
    requester: Optional[str] = None

    def to_dict(self):
        try:
            return self.model_dump()
        except Exception as e:
            raise ValueError(f"Failed to convert object to dictionary: {e}")

    @classmethod
    def from_dict(cls, data: Dict) -> "TaskInfo":
        """Create TaskInfo from dictionary."""
        try:
            return parse_obj_as(cls, data)
        except ValidationError as e:
            raise ValueError(f"Invalid input dictionary: {e}")


class Collaboration(Registrable, metaclass=ABCMeta):
    """Base class for collaboration strategies between agents.

    This class defines the interface for different collaboration strategies that can be
    implemented between agents in the chorus system. Collaboration strategies determine
    how agents work together and communicate.
    """

    def __init__(self):
        self._team_info = None
        self._services = []

    @abstractmethod
    def process_message(
        self, team_context: "TeamContext", team_state: "TeamState", inbound_message: Message
    ):
        """
        Processes an inbound message for the team.
        """

    def iterate(self, team_context: "TeamContext", team_state: "TeamState") -> "TeamState":
        """
        Iterates the collaboration strategy.
        """
        return team_state

    def list_utilities(self):
        """
        Returns a list of utilities provided by the collaboration.
        """

    def get_name(self):
        """
        Get the name of the collaboration.
        """
        return self.__class__.__name__

    def register_team(self, team_info: TeamInfo, services: Optional[List["TeamService"]] = None):
        """
        Register services with the collaboration.
        """
        self._team_info = team_info
        self._services = services

    def list_services(self) -> List["TeamService"]:
        """
        List all services registered with the collaboration.
        """
        return self._services

    def get_team_info(self) -> TeamInfo:
        """
        Get the team info.
        """
        return self._team_info
