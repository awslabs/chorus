from abc import abstractmethod, ABCMeta
from typing import List, Optional
from chorus.agents import PassiveAgent
from chorus.data.team_info import TeamInfo
from chorus.data.state import TeamState
from chorus.data.context import TeamContext

class BaseTeam(PassiveAgent[TeamContext, TeamState], metaclass=ABCMeta):
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
