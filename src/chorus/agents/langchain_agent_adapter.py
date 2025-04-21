import logging
from typing import Any, List, Optional, Type, Dict, Callable, TYPE_CHECKING, ClassVar
import json

if TYPE_CHECKING:
    from langchain.agents import AgentExecutor, BaseSingleActionAgent  # type: ignore
    from langchain.schema import AgentAction, AgentFinish  # type: ignore
    from langchain.callbacks.base import BaseCallbackHandler  # type: ignore
    from langchain.callbacks.manager import CallbackManager  # type: ignore

from chorus.agents.passive_agent import PassiveAgent
from chorus.data.context import AgentContext
from chorus.data.dialog import Message, EventType
from chorus.data.state import AgentState, PassiveAgentState
from chorus.communication.message_service import DEFAULT_ROUTER_PORT

logger = logging.getLogger(__name__)


class LangChainAgentState(PassiveAgentState):
    """State for the LangChain agent adapter.
    
    Extends PassiveAgentState to add fields for storing LangChain-specific data.
    """
    langchain_memory: Dict[str, Dict[str, Any]] = {}
    
    def clone(self) -> "LangChainAgentState":
        """Create a deep copy of this state."""
        new_state = LangChainAgentState()
        # Deep copy the memory dictionary
        new_state.langchain_memory = json.loads(json.dumps(self.langchain_memory))
        return new_state


class ChorusCallbackHandler:
    """Callback handler for LangChain agents that logs to the Chorus environment."""
    
    _callback_handler_class: ClassVar[Optional[Type]] = None
    
    def __new__(cls, *args, **kwargs):
        # Import BaseCallbackHandler here to avoid requiring langchain as a dependency
        # when not using LangChain agents
        try:
            from langchain.callbacks.base import BaseCallbackHandler
            
            # Only create the dynamic class once
            if cls._callback_handler_class is None:
                # Create a dynamic class that inherits from BaseCallbackHandler
                cls._callback_handler_class = type(
                    'DynamicChorusCallbackHandler',
                    (BaseCallbackHandler,),
                    {k: v for k, v in cls.__dict__.items() if k != '__new__'}
                )
            
            # Create an instance of the dynamic class
            return object.__new__(cls._callback_handler_class)
        except ImportError:
            # For testing, we might be using a mock BaseCallbackHandler
            # Just return a standard object in that case
            logging.info("Using mock callback handler for testing")
            return object.__new__(cls)
    
    def __init__(self, context: AgentContext, source: str = "langchain", channel: Optional[str] = None):
        """Initialize the callback handler."""
        self.context = context
        self.source = source
        self.channel = channel
        self.logger = logging.getLogger(__name__)

    def on_agent_action(self, action: Any, **kwargs) -> None:
        """Log the agent's action to the Chorus environment.

        Args:
            action: The action the agent is about to take.
            **kwargs: Additional arguments.
        """
        if self.context.message_client is None:
            raise RuntimeError("Message client not initialized.")
        # Send an internal event to log the action
        self.context.message_client.send_message(
            Message(
                source=self.context.agent_id,
                destination=self.context.agent_id,
                content=f"Tool: {action.tool}\nInput: {action.tool_input}",
                event_type=EventType.INTERNAL_EVENT,
            )
        )

    def on_agent_finish(self, finish: Any, **kwargs) -> None:
        """Log the agent's final output to the Chorus environment.

        Args:
            finish: The final output of the agent.
            **kwargs: Additional arguments.
        """
        if self.context.message_client is None:
            raise RuntimeError("Message client not initialized.")
        # This is just for logging, the actual response is sent elsewhere
        self.context.message_client.send_message(
            Message(
                source=self.context.agent_id,
                destination=self.context.agent_id,
                content=f"Agent finished: {finish.return_values}",
                event_type=EventType.INTERNAL_EVENT,
            )
        )


class LangChainAgentAdapter(PassiveAgent):
    """An adapter that wraps a LangChain agent for use within the Chorus framework.

    This adapter translates between the Chorus message format and the LangChain
    agent's expected input/output format, allowing LangChain agents to be used
    within the Chorus framework.

    Note: This adapter requires LangChain to be installed. If not already installed,
    install it with `pip install langchain`.

    The recommended way to use this adapter is with the factory pattern:

    ```python
    class MyAgent(LangChainAgentAdapter):
        @staticmethod
        def create_agent():
            # This runs in the worker process, avoiding pickling issues
            tools = [Tool(...), ...]
            llm = SomeLLM()  # Can have unpicklable objects like API clients
            return initialize_agent(tools, llm, ...)
            
        def __init__(self):
            super().__init__(agent_factory=self.create_agent)
    ```

    Args:
        agent_factory: Function that returns a LangChain AgentExecutor.
            This will be called during initialization in the worker process.
            Using a factory avoids pickling issues with unpicklable objects.
        preserve_history: Whether to preserve conversation history between calls.
        no_response_sources: Optional list of source IDs that this agent should ignore
            messages from.
    """

    def __init__(
        self,
        agent_factory: Callable[[], Any],  # AgentExecutor
        preserve_history: bool = True,
        no_response_sources: Optional[List[str]] = None,
    ):
        # First check if langchain is installed
        try:
            import langchain  # type: ignore
            self._langchain_available = True
        except ImportError:
            logger.error("LangChain not installed. Please install it with `pip install langchain`")
            self._langchain_available = False
            raise ImportError("LangChain is required for LangChainAgentAdapter but not installed. "
                              "Please install it with `pip install langchain`")
        
        super().__init__(no_response_sources=no_response_sources)
        self._agent_factory = agent_factory
        self._preserve_history = preserve_history
        self._initialized = False
        self._langchain_agent = None
        self._agent_executor = None

    def _ensure_initialized(self):
        """Ensure the agent is initialized by using the factory."""
        if not self._initialized:
            logger.info(f"Initializing LangChain agent via factory for {self.identifier()}")
            executor = self._agent_factory()
            self._agent_executor = executor
            self._langchain_agent = executor.agent
            self._initialized = True

    def _ensure_message_client(self, context: AgentContext) -> bool:
        """Ensure the context has a valid message client.
        
        Args:
            context: The agent's context
            
        Returns:
            bool: True if the message client is valid, False otherwise
        """
        if not hasattr(context, 'message_client') or context.message_client is None:
            logger.error(f"Agent {self.identifier()} has no message client in context")
            return False
        return True
        
    def run(self, router_host: str = "localhost", router_port: int = DEFAULT_ROUTER_PORT, 
            context: Optional[AgentContext] = None, state: Optional[AgentState] = None):
        """Run the agent in a continuous loop, initializing it first if needed."""
        # Initialize the agent with factory if needed, now that we're in the worker process
        self._ensure_initialized()
        # Continue with normal run process
        super().run(router_host, router_port, context, state)

    def init_state(self) -> LangChainAgentState:
        """Initialize the agent's state.

        Returns:
            LangChainAgentState: A new state object for this agent.
        """
        return LangChainAgentState()

    def respond(
        self, context: AgentContext, state: LangChainAgentState, inbound_message: Message
    ) -> LangChainAgentState:
        """Process and respond to an incoming message using the LangChain agent.

        This method adapts between the Chorus message interface and LangChain's input/output format.
        
        Args:
            context: The agent's context containing environmental information.
            state: The current state of the agent.
            inbound_message: The message to respond to.

        Returns:
            LangChainAgentState: The updated agent state after processing the message.
        """
        # Ensure initialization if it hasn't happened yet (e.g., if run() wasn't called)
        self._ensure_initialized()
        if self._langchain_agent is None:
            raise RuntimeError("LangChain agent is not initialized.")
        
        # Check if we have a valid message client
        if not self._ensure_message_client(context):
            logger.error("Cannot respond without a valid message client")
            return state
        
        # Extract the inbound source to respond to
        inbound_source = inbound_message.source
        inbound_channel = inbound_message.channel
        
        # Create a callback handler for this interaction
        callback_handler = ChorusCallbackHandler(
            context=context,
            source=inbound_source,
            channel=inbound_channel
        )
        
        # Add the callback handler temporarily
        if hasattr(self._agent_executor, 'callbacks') and self._agent_executor.callbacks:
            self._agent_executor.callbacks.add_handler(callback_handler)
        
        # Parse the content based on the event type
        if inbound_message.event_type == EventType.MESSAGE:
            # For simple messages, use the content directly
            input_text = inbound_message.content
        else:
            # For other event types, we may need more complex parsing
            # This is a simplified implementation
            input_text = f"{inbound_message.event_type}: {inbound_message.content}"
        
        # Create input dict with conversation ID for memory
        conversation_id = f"{inbound_source}-{context.agent_id}"
        
        # Retrieve or initialize conversation memory
        if self._preserve_history and conversation_id in state.langchain_memory:
            memory = state.langchain_memory[conversation_id]
            # Make sure the current input is used rather than any previous input
            memory_without_input = {k: v for k, v in memory.items() if k != "input"}
            inputs = {"input": input_text, **memory_without_input}
            logger.debug(f"Using existing memory for conversation {conversation_id}: {memory}")
        else:
            inputs = {"input": input_text}
            logger.debug(f"No existing memory for conversation {conversation_id}, using fresh inputs")
        
        # Log the input for debugging
        logger.info(f"Agent input: {inputs}")
        
        # Execute the LangChain agent with the input
        try:
            agent_output = self._agent_executor.run(inputs)
            
            # Log the output for debugging
            logger.info(f"Agent output: {agent_output}")
            
            # If we're preserving history, update the memory
            if self._preserve_history:
                # A simple implementation - in practice, you might want to use
                # LangChain's built-in memory classes
                memory = inputs.copy()
                memory["chat_history"] = memory.get("chat_history", []) + [
                    (input_text, agent_output)
                ]
                state.langchain_memory[conversation_id] = memory
                logger.debug(f"Updated memory for conversation {conversation_id}: {memory}")
            
            # Create response message
            response_message = Message(
                source=context.agent_id,
                destination=inbound_source,
                channel=inbound_channel,
                content=agent_output,
                event_type=EventType.MESSAGE,
            )
            
            # Send the response
            context.message_client.send_message(response_message)
            
        except Exception as e:
            logger.error(f"Error executing LangChain agent: {e}")
            # Send error message
            error_message = Message(
                source=context.agent_id,
                destination=inbound_source,
                channel=inbound_channel,
                content=f"Sorry, I encountered an error: {str(e)}",
                event_type=EventType.MESSAGE,
            )
            context.message_client.send_message(error_message)
        finally:
            # Remove the temporary callback handler
            if hasattr(self._agent_executor, 'callbacks') and self._agent_executor.callbacks:
                self._agent_executor.callbacks.remove_handler(callback_handler)
        
        return state 