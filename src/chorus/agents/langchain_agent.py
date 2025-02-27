
import logging
from chorus.agents.base import Agent
from chorus.agents.passive_agent import PassiveAgent
from chorus.data.context import AgentContext
from chorus.data.dialog import Message
from chorus.data.state import LangchainAgentState
from langchain.agents import AgentExecutor

logger = logging.getLogger(__name__)

@Agent.register("LangChainAgent")
class LangChainAgent(PassiveAgent):
    def __init__(
        self,   
        name: str,
        langchain_agent: AgentExecutor):
        """
        Initialize Langchain Agent
        
        Args:
            langchain_config: LangChain configuration
        """

        super().__init__()

        self.langchain_agent = langchain_agent
        self._name = name

    def init_context(self) -> AgentContext:
        """Initialize the agent's context with agent name
        Returns:
            AgentContext: A new context object containing the agent's configuration.
        """
        context = AgentContext(
            agent_id=self._name
        )
        return context

    def init_state(self) -> LangchainAgentState:
        memory = self.langchain_agent.memory
        return LangchainAgentState(memory)

    def respond(
        self, state: LangchainAgentState, inbound_message: Message
    ) -> LangchainAgentState:
        """Process and respond to an incoming message.
        Args:
            context: The agent's context containing environmental information.
            state: The current state of the passive agent.
            inbound_message: The message to respond to.
        Returns:
            PassiveAgentState: The updated agent state after processing the message.
        """
        logging.info(f"LangChainAgent received message: {inbound_message} state {state}")
        query = inbound_message.content
        conversation_context = state.get_conversation_context(query)
        if conversation_context:
            query = f"Context: {conversation_context}\nQuery: {query}"
        agent_response = self.langchain_agent.run(query)
        state.save_conversation_context(inbound_message.content, agent_response)
        return agent_response
