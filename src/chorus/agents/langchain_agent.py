from typing import Optional
from chorus.agents.base import Agent
from chorus.agents.passive_agent import PassiveAgent
from chorus.data.context import AgentContext
from chorus.data.dialog import Message
from chorus.data.state import PassiveAgentState

try:
    from langchain.agents import AgentExecutor
    from langchain_core.memory import BaseMemory
    HAVE_LANGCHAIN = True
except ImportError as e:
    HAVE_LANGCHAIN = False

class LangchainAgentState(PassiveAgentState):
    memory: Optional["BaseMemory"] = None  # type: ignore


@Agent.register("LangChainAgent")
class LangChainAgent(PassiveAgent):
    def __init__(
        self,   
        name: str,
        langchain_agent: "AgentExecutor"):  # type: ignore
        """
        Initialize Langchain Agent
        
        Args:
            langchain_config: LangChain configuration
            
        Raises:
            ImportError: If langchain is not installed
        """
        if not HAVE_LANGCHAIN:
            raise ImportError(
                "Could not import langchain. Please install chorus with langchain option"
                " to use the LangChainAgent."
            )
        
        super().__init__(name)
        self.langchain_agent = langchain_agent

    def init_state(self) -> LangchainAgentState:
        """Initialize the agent's state.

        Returns:
            LangchainAgentState: A new state object for this Langchain agent.
        """
        state = LangchainAgentState()
        if hasattr(self.langchain_agent, 'memory'):
            state.memory = self.langchain_agent.memory
        return state
    def respond(
        self, context: AgentContext, state: LangchainAgentState, inbound_message: Message
    ) -> LangchainAgentState:
        """Process and respond to an incoming message.

        Args:
            context: The agent's context containing environmental information.
            state: The current state of the passive agent.
            inbound_message: The message to respond to.

        Returns:
            PassiveAgentState: The updated agent state after processing the message.
        """
        # Recover memory from state
        if state.memory is not None:
            self.langchain_agent.memory = state.memory

        query = inbound_message.content
        agent_response = self.langchain_agent.run(query)
        if agent_response is not None:
            if isinstance(agent_response, str): 
                context.get_message_service().send_message(Message(
                    destination=inbound_message.source,
                    source=context.agent_id,
                    channel=inbound_message.channel,
                    content=agent_response
                ))
            else:
                raise ValueError(f"Agent response is not a string: {agent_response}")

        # Save memory back to state
        if hasattr(self.langchain_agent, 'memory'):
            state.memory = self.langchain_agent.memory

        return state