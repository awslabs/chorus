from abc import abstractmethod, ABCMeta
from typing import List, Optional
from chorus.agents import PassiveAgent
from chorus.data.team_info import TeamInfo
from chorus.data.state import TeamState
from chorus.data.context import TeamContext

class BaseTeam(PassiveAgent[TeamContext, TeamState]):
    """
    A team of agents that collaborate to achieve a goal.
    """
    
    def name_to_identifier(self, name: str) -> str:
        """Convert a name to an identifier.
        
        Args:
            name (str): The name to convert.
        """
        return f"team:{name}"
    
    @abstractmethod
    def get_team_info(self, agent_ids: Optional[List[str]] = None) -> TeamInfo:
        """
        Get the team information.
        """