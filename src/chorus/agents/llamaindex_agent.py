import logging
from llama_index.core.agent import ReActAgent
from chorus.agents.base import Agent
from chorus.agents.passive_agent import PassiveAgent
from chorus.data.context import AgentContext
from chorus.data.dialog import Message, Role
from chorus.data.state import PassiveAgentState

logger = logging.getLogger(__name__)

@Agent.register("LlamaIndexAgent")
class LlamaIndexAgent(PassiveAgent):
    """A passive agent that uses a LlamaIndex agent to respond to messages.
    """

    def __init__(
        self,  
        name: str,
        llamaindexAgent: ReActAgent,
    ):
        super().__init__()
        self.llamaindex_agent = llamaindexAgent
        self._name = name

    def respond(
        self, context: AgentContext, state: PassiveAgentState, inbound_message: Message
    ) -> PassiveAgentState:
        """Process and respond to an incoming message using the LlamaIndex agent.

        Args:
            context: The agent's context containing environmental information.
            state: The current state of the passive agent.
            inbound_message: The message to respond to.

        Returns:
            PassiveAgentState: The updated agent state after processing the message.
        """
        response = self.llamaindex_agent.chat(inbound_message.content)
        context.message_service.send_message(
            Message(
                source=context.agent_id,
                destination=inbound_message.source,
                content=response.response,
                role=Role.OBSERVATION,
            )
        )
        return state