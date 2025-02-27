from typing import List, Optional
from chorus.agents import Agent, PassiveAgent
from chorus.collaboration import Collaboration
from chorus.data.dialog import Message
from chorus.data.state import PassiveAgentState, TeamState
from chorus.data.team_info import TeamInfo
from chorus.data.context import AgentContext, TeamContext
from chorus.teams.base import BaseTeam
from chorus.teams.services.base import TeamService

@BaseTeam.register("Team")
class Team(BaseTeam):
    """
    A team of agents that collaborate to achieve a goal.
    """

    def respond(self, context: TeamContext, state: TeamState, inbound_message: Message) -> TeamState:
        if inbound_message.event_type == "team_service":
            for service in self._services:
                service.process_message(context, state, inbound_message)
        else:
            self._collaboration.process_message(context, state, inbound_message)
        return state
    
    def iterate(self, context: TeamContext, state: TeamState) -> Optional[PassiveAgentState]:
        if self._collaboration:
            state = self._collaboration.iterate(context, state)
        return super().iterate(context, state)

    def init_context(self) -> TeamContext:
        return TeamContext(agent_id=f"team:{self._name}")
    
    def init_state(self) -> TeamState:
        state = TeamState()
        self._collaboration.register_team(self._team_info, self._services)
        for service in self._services:
            service.register_team(self._team_info, self._services)
            service.initialize_service(state)
        return state

    def __init__(self, name: str, agents: List[Agent], collaboration: Collaboration, services: Optional[List[TeamService]] = None):
        """
        Initialize a team.
        
        Args:
            name: The name of the team.
            agents: The agents of the team.
            collaboration: The collaboration of the team.
            services: The services of the team.
        """
        super().__init__()
        self._name = name
        self._agents = agents
        self._collaboration = collaboration
        self._services = services if services is not None else []
        self._team_info = TeamInfo(
            name=self._name,
            agent_ids=None,
            collaboration_name=self._collaboration.get_name(),
            service_names=[service.get_name() for service in self._services]
        )
    
    def get_team_info(self, agent_ids: Optional[List[str]] = None) -> TeamInfo:
        self._team_info.agent_ids = agent_ids
        return self._team_info

    def get_name(self):
        """
        Get the name of the team.
        """
        return self._name

    def get_collaboration(self):
        """
        Get the collaboration of the team.
        """
        return self._collaboration

    def get_agents(self):
        """
        Get the agents of the team.
        """
        return self._agents
    
    def get_identifier(self):
        """
        Get the network identifier of the team.
        """
        return f"team:{self._name}"
    
    def add_agent(self, agent: Agent):
        """
        Add an agent to the team.
        """
        self._agents.append(agent)
    
    def list_services(self):
        """
        List the services of the team.
        """
        return self._services
