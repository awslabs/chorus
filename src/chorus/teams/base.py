from abc import abstractmethod, ABCMeta
from typing import List, Optional
from chorus.agents import Agent, PassiveAgent
from chorus.collaboration import Collaboration
from chorus.config.registrable import Registrable
from chorus.data.dialog import Message
from chorus.data.state import TeamState
from chorus.data.team_info import TeamInfo
from chorus.data.context import TeamContext
from chorus.teams.services.base import TeamService

class BaseTeam(PassiveAgent, metaclass=ABCMeta):
    """
    A team of agents that collaborate to achieve a goal.
    """
    
    @abstractmethod
    def get_team_info(self, agent_ids: Optional[List[str]] = None) -> TeamInfo:
        """
        Get the team information.
        """

    @abstractmethod
    def get_name(self):
        """
        Get the name of the team.
        """
    
    def get_identifier(self):
        """
        Get the network identifier of the team.
        """
        return f"team:{self.get_name()}"
