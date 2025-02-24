from abc import abstractmethod, ABCMeta
from typing import List, Optional

from chorus.config.registrable import Registrable
from chorus.data.state import TeamState
from chorus.data.dialog import Message
from chorus.data.context import TeamContext
from chorus.data.team_info import TeamInfo

class TeamService(Registrable, metaclass=ABCMeta):

    def __init__(self, service_name: str):
        self._service_name = service_name
        self._team_info: Optional[TeamInfo] = None
        self._services: Optional[List["TeamService"]] = None

    def get_name(self) -> str:
        """
        Return the name of team services.
        """
        return self._service_name

    def initialize_service(self, team_state: TeamState):
        """
        Initialize the service with the team state.
        """


    @abstractmethod
    def process_message(self, team_context: TeamContext, team_state: TeamState, inbound_message: Message):
        """
        Process an message and update the team state accordingly.
        """

    def register_team(self, team_info: Optional[TeamInfo] = None, services: Optional[List["TeamService"]] = None):
        """
        Register the team info and services with the collaboration.
        """
        self._team_info = team_info
        self._services = services
    
    def get_team_info(self) -> Optional[TeamInfo]:
        """
        Return the team info.
        """
        return self._team_info
    
    def get_services(self) -> Optional[List["TeamService"]]:
        """
        Return the services.
        """
        return self._services

