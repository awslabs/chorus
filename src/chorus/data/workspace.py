from typing import List, Optional

from jupyter_core.migrate import security_file

from chorus.agents import Agent
from chorus.config.from_params import FromParams
from chorus.teams.base import BaseTeam


class Workspace(FromParams):
    """A workspace that contains agents and teams for collaboration.

    The workspace manages agents, teams, communication channels and execution conditions.
    It serves as the main container and coordination point for agent interactions.

    Attributes:
        agents: List of Agent objects that can interact in the workspace
        teams: List of BaseTeam objects that group agents together
        channels: List of communication channel names
        main_channel: Primary channel for communication
        stop_conditions: Conditions that will halt workspace execution
        start_messages: Initial messages to populate the workspace
        title: Title of the workspace
        description: Description of the workspace
    """

    def __init__(
        self,
        agents: Optional[List[Agent]] = None,
        teams: Optional[List[BaseTeam]] = None,
        channels: Optional[List[str]] = None,
        main_channel: Optional[str] = None,
        stop_conditions=None,
        start_messages=None,
        title="",
        description="",
    ):
        """Initialize a new Workspace.

        Args:
            agents: List of agents to add to the workspace
            teams: List of teams to add to the workspace
            channels: List of communication channel names
            main_channel: Primary channel for communication
            stop_conditions: Conditions that will halt workspace execution
            start_messages: Initial messages to populate the workspace
            title: Title of the workspace
            description: Description of the workspace

        Raises:
            ValueError: If neither agents nor teams are provided
        """
        if not agents and not teams:
            raise ValueError("At least one agent or team must be provided for creating a workspace.")
        self.start_messages = start_messages if start_messages else []
        self.agents = agents
        self.teams = teams
        self.channels = channels
        self.stop_conditions = stop_conditions
        self.main_channel = main_channel
        self._infer_main_channel()

    def _infer_main_channel(self):
        """Infer and set the main communication channel if not explicitly specified.
        
        If main_channel is not set, attempts to set it based on the first team
        or first agent in the workspace. For teams, uses format "team:{team_name}".
        For agents, uses format "agent:{agent_id}".
        """
        if self.main_channel is not None:
            return
        elif self.teams:
            self.main_channel = "team:{}".format(self.teams[0].get_name())
        elif self.agents:
            first_agent = self.agents[0]
            context = first_agent.init_context()
            self.main_channel = "agent:{}".format(context.agent_id)
