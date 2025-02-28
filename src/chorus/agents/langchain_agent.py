from typing import Optional, Callable
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
        init_agent_func: Callable[["BaseMemory"], "AgentExecutor"],
        init_memory_func: Callable[[], "BaseMemory"]):  # type: ignore
        """
        Initialize Langchain Agent
        
        Args:
            name: Name of the agent
            init_agent_func: Function that takes a memory instance and returns a LangChain AgentExecutor
            init_memory_func: Function that creates and returns LangChain Memory
            
        Raises:
            ImportError: If langchain is not installed
        """
        if not HAVE_LANGCHAIN:
            raise ImportError(
                "Could not import langchain. Please install chorus with langchain option"
                " to use the LangChainAgent."
            )
        
        super().__init__(name)
        self._init_agent_func = init_agent_func
        self._init_memory_func = init_memory_func
        self.langchain_agent = None

    def _ensure_agent_initialized(self, memory: "BaseMemory"):
        """Ensures the LangChain agent is initialized in the current process.
        
        Args:
            memory: The memory instance to use for agent initialization
        """
        if self.langchain_agent is None:
            self.langchain_agent = self._init_agent_func(memory)

    def init_state(self) -> LangchainAgentState:
        """Initialize the agent's state.

        Returns:
            LangchainAgentState: A new state object for this Langchain agent.
        """
        state = LangchainAgentState()
        state.memory = self._init_memory_func()
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
        # Initialize agent if needed with current memory
        if state.memory is None:
            state.memory = self._init_memory_func()
        self._ensure_agent_initialized(state.memory)

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
            state.memory = self.langchain_agent.memory.model_copy()

        return state