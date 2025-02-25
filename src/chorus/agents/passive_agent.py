import abc
import logging
from typing import List
from typing import Optional


from chorus.agents.base import Agent
from chorus.data.context import AgentContext
from chorus.data.agent_status import AgentStatus
from chorus.data.dialog import Message
from chorus.data.dialog import Role
from chorus.data.state import PassiveAgentState

logger = logging.getLogger(__name__)


class PassiveAgent(Agent, metaclass=abc.ABCMeta):
    """Base class for passive agents that respond to incoming messages.

    A passive agent waits for messages directed to it and responds accordingly. Unlike active
    agents, it does not initiate interactions on its own.

    Args:
        name: Optional name for the agent. If not provided, a default name will be generated.
        no_response_sources: Optional list of source IDs that this agent should ignore
            messages from.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        no_response_sources: Optional[List[str]] = None,
    ):
        super().__init__(name)
        self._no_response_sources = no_response_sources

    def init_state(self) -> PassiveAgentState:
        """Initialize the agent's state.

        Returns:
            PassiveAgentState: A new state object for this passive agent.
        """
        return PassiveAgentState()

    @abc.abstractmethod
    def respond(
        self, context: AgentContext, state: PassiveAgentState, inbound_message: Message
    ) -> PassiveAgentState:
        """Process and respond to an incoming message.

        Args:
            context: The agent's context containing environmental information.
            state: The current state of the passive agent.
            inbound_message: The message to respond to.

        Returns:
            PassiveAgentState: The updated agent state after processing the message.
        """
        pass

    def iterate(
        self, context: AgentContext, state: Optional[PassiveAgentState]
    ) -> Optional[PassiveAgentState]:
        """Execute one iteration of the agent's message processing loop.

        Checks for new messages directed to this agent and processes the first valid one found.
        A message is valid if:
        - It is directed to this agent
        - It hasn't been processed before
        - It is not an ACTION or OBSERVATION
        - Its source is not in no_response_sources

        Args:
            context: The agent's context containing environmental information.
            state: The current state of the passive agent.

        Returns:
            Optional[PassiveAgentState]: The updated agent state if a message was processed,
                or the unchanged state if no valid messages were found.
        """
        all_messages = context.message_service.fetch_all_messages()
        new_incoming_msg = None
        agent_id = context.agent_id
        for msg in all_messages:
            if (
                (msg.destination == agent_id or msg.channel is not None)
                and msg.message_id not in state.processed_messages
                and msg.role not in (Role.ACTION, Role.OBSERVATION)
            ):
                if (
                    self._no_response_sources is not None
                    and msg.source in self._no_response_sources
                ):
                    continue
                new_incoming_msg = msg
                break
        if new_incoming_msg is not None:
            logger.info(f"==== Passive Agent Responding: {agent_id} ====")
            logger.info("All messages:")
            logger.info(
                ", ".join(
                    [
                        f"[{msg.channel if msg.channel is not None else 'DM'}] {msg.source}->{msg.destination}:{msg.role}:{msg.message_id}"
                        for msg in all_messages
                    ]
                )
            )
            logger.info(f"Inbound message: {new_incoming_msg.model_dump_json(indent=2)}")
            logger.info("==== *** ====")

            state.processed_messages.add(new_incoming_msg.message_id)
            context.report_status(context.agent_id, AgentStatus.BUSY)
            downstream_state = self.respond(context, state, new_incoming_msg)
            context.report_status(context.agent_id, AgentStatus.AVAILABLE)
            return downstream_state if downstream_state is not None else state
        else:
            return state
