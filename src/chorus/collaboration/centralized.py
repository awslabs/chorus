from chorus.collaboration.base import Collaboration
from chorus.data.dialog import Message
from chorus.helpers.communication import CommunicationHelper

from chorus.data.context import TeamContext
from chorus.data.state import TeamState


@Collaboration.register('CentralizedCollaboration')
class CentralizedCollaboration(Collaboration):
    """Implements a centralized collaboration strategy between agents.

    This strategy coordinates multiple agents through a central coordinator that manages
    communication and task distribution.

    """

    def process_message(self, team_context: TeamContext, team_state: TeamState, inbound_message: Message):
        if inbound_message.event_type == "team_service":
            return
        requester = inbound_message.source
        if team_context.team_info is not None:
            if requester not in team_context.team_info.agent_ids:
                return
        helper = CommunicationHelper(team_context)
        helper.send(self._coordinator, inbound_message.content, source=requester)
        return

    def __init__(self, coordinator: str):
        """Initialize the centralized collaboration strategy.

        Args:
            coordinator (Agent): The coordinator agent that will manage collaboration.
        """
        super().__init__()
        self._coordinator = coordinator

    def get_coordinator(self):
        return self._coordinator

    def get_name(self):
        return "centaralized"