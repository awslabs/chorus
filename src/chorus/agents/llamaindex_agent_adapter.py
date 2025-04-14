import logging
from typing import Any, List, Optional, Type, Dict, Union, Callable, TYPE_CHECKING, ClassVar
import json
import asyncio

from chorus.agents.passive_agent import PassiveAgent
from chorus.data.context import AgentContext
from chorus.data.dialog import Message, EventType
from chorus.data.state import AgentState, PassiveAgentState
from chorus.data.executable_tool import ExecutableTool
from pydantic import Field
from chorus.communication.message_service import DEFAULT_ROUTER_PORT

logger = logging.getLogger(__name__)

# Check if LlamaIndex is available
LLAMAINDEX_AVAILABLE = False
try:
    import llama_index
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    logger.debug("LlamaIndex not installed. LlamaIndexAgentAdapter will be available but requires llama-index to function.")


# Define a custom state class for LlamaIndex agent
class LlamaIndexAgentState(PassiveAgentState):
    """State for the LlamaIndex agent adapter.
    
    Extends PassiveAgentState to add fields for storing LlamaIndex-specific data.
    """
    llamaindex_memory: Dict[str, Dict[str, Any]] = {}
    
    def clone(self) -> "LlamaIndexAgentState":
        """Create a deep copy of this state."""
        new_state = LlamaIndexAgentState()
        # Deep copy the memory dictionary
        new_state.llamaindex_memory = json.loads(json.dumps(self.llamaindex_memory))
        return new_state


class ChorusLlamaIndexCallbackHandler:
    """Callback handler for LlamaIndex agents that logs to the Chorus environment."""
    
    def __init__(self, context: AgentContext, source: str = "llamaindex", channel: Optional[str] = None):
        """Initialize the callback handler."""
        self.context = context
        self.source = source
        self.channel = channel
        self.logger = logging.getLogger(__name__)

    # Implementation of handler methods
    def on_agent_action(self, action: Any, **kwargs) -> None:
        """Log the agent's action to the Chorus environment."""
        tool_name = getattr(action, "tool", "unknown tool")
        tool_input = getattr(action, "input", "unknown input")
        
        self.context.message_client.send_message(
            Message(
                source=self.context.agent_id,
                destination=self.context.agent_id,
                content=f"Tool: {tool_name}\nInput: {tool_input}",
                event_type=EventType.INTERNAL_EVENT,
            )
        )

    def on_agent_finish(self, response: Any, **kwargs) -> None:
        """Log the agent's final output to the Chorus environment."""
        self.context.message_client.send_message(
            Message(
                source=self.context.agent_id,
                destination=self.context.agent_id,
                content=f"Agent finished: {response}",
                event_type=EventType.INTERNAL_EVENT,
            )
        )
    
    # Empty implementations for callbacks we don't use
    def on_event_start(self, event_type: str, payload: Dict[str, Any], **kwargs) -> None:
        """Handle event start."""
        pass
    
    def on_event_end(self, event_type: str, payload: Dict[str, Any], **kwargs) -> None:
        """Handle event end."""
        pass
    
    def start_trace(self, trace_id: str, **kwargs) -> None:
        """Start a trace."""
        pass
    
    def end_trace(self, trace_id: str, **kwargs) -> None:
        """End a trace."""
        pass


class LlamaIndexAgentAdapter(PassiveAgent):
    """An adapter that wraps a LlamaIndex agent for use within the Chorus framework.

    This adapter translates between the Chorus message format and the LlamaIndex
    agent's expected input/output format, allowing LlamaIndex agents to be used
    within the Chorus framework.

    Note: This adapter requires LlamaIndex to be installed. If not already installed,
    install it with `pip install llama-index`.

    The recommended way to use this adapter is with the factory pattern:

    ```python
    class MyAgent(LlamaIndexAgentAdapter):
        @staticmethod
        def create_agent():
            # This runs in the worker process, avoiding pickling issues
            tools = [Tool(...), ...]
            llm = SomeLLM()  # Can have unpicklable objects like API clients
            return ReActAgent.from_tools(tools=tools, llm=llm, ...)
            
        def __init__(self):
            super().__init__(agent_factory=self.create_agent)
    ```

    For AWS Bedrock Converse, you can create a simple agent directly:
    
    ```python
    class MyBedrockAgent(LlamaIndexAgentAdapter):
        @staticmethod
        def create_agent():
            # Create Bedrock Converse LLM
            llm = BedrockConverse(
                model="anthropic.claude-3-haiku-20240307-v1:0",
                aws_access_key_id="YOUR_KEY",
                aws_secret_access_key="YOUR_SECRET",
                region_name="us-east-1",
            )
            
            # Create a simple agent
            return SimpleCalculatorAgent(llm)
            
        def __init__(self):
            super().__init__(agent_factory=self.create_agent)
    ```

    Args:
        agent_factory: Function that returns a LlamaIndex agent with a 'run' method.
            This will be called during initialization in the worker process.
            Using a factory avoids pickling issues with unpicklable objects.
        preserve_history: Whether to preserve conversation history between calls.
        no_response_sources: Optional list of source IDs that this agent should ignore
            messages from.
    """

    def __init__(
        self,
        agent_factory: Callable[[], Any],  # LlamaIndex Agent (e.g., ReActAgent, FunctionAgent)
        preserve_history: bool = True,
        no_response_sources: Optional[List[str]] = None,
    ):
        # Check if LlamaIndex is installed - we do this at initialization time to
        # allow the class to be imported/referenced even if LlamaIndex is not installed
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndex is required for LlamaIndexAgentAdapter but not installed. "
                "Please install it with `pip install llama-index` or "
                "`pip install chorus[llamaindex]`"
            )
        
        super().__init__(no_response_sources=no_response_sources)
        self._agent_factory = agent_factory
        self._preserve_history = preserve_history
        self._initialized = False
        self._llamaindex_agent = None

    def _ensure_initialized(self):
        """Ensure the agent is initialized by using the factory."""
        if not self._initialized:
            logger.info(f"Initializing LlamaIndex agent via factory for {self.identifier()}")
            self._llamaindex_agent = self._agent_factory()
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

    def init_state(self) -> LlamaIndexAgentState:
        """Initialize the agent's state.

        Returns:
            LlamaIndexAgentState: A new state object for this agent.
        """
        return LlamaIndexAgentState()

    def _is_function_agent(self) -> bool:
        """Check if the agent is a FunctionAgent."""
        try:
            try:
                from llama_index.core.agent.workflow import FunctionAgent
                return isinstance(self._llamaindex_agent, FunctionAgent)
            except ImportError:
                from llama_index.agent.workflow import FunctionAgent
                return isinstance(self._llamaindex_agent, FunctionAgent)
        except (ImportError, TypeError):
            # If we can't import or if isinstance throws an error
            return False

    def respond(
        self, context: AgentContext, state: LlamaIndexAgentState, inbound_message: Message
    ) -> LlamaIndexAgentState:
        """Process and respond to an incoming message using the LlamaIndex agent.

        This method adapts between the Chorus message interface and LlamaIndex's input/output format.
        
        Args:
            context: The agent's context containing environmental information.
            state: The current state of the agent.
            inbound_message: The message to respond to.

        Returns:
            LlamaIndexAgentState: The updated agent state after processing the message.
        """
        # Ensure initialization if it hasn't happened yet (e.g., if run() wasn't called)
        self._ensure_initialized()
        
        # Check if we have a valid message client
        if not self._ensure_message_client(context):
            logger.error("Cannot respond without a valid message client")
            return state
        
        # Extract the inbound source to respond to
        inbound_source = inbound_message.source
        inbound_channel = inbound_message.channel
        
        # Create a simple callback handler for logging only
        callback_handler = ChorusLlamaIndexCallbackHandler(
            context=context,
            source=inbound_source,
            channel=inbound_channel
        )
        
        # Parse the content based on the event type
        if inbound_message.event_type == EventType.MESSAGE:
            # For simple messages, use the content directly
            input_text = inbound_message.content
        else:
            # For other event types, we may need more complex parsing
            # This is a simplified implementation
            input_text = f"{inbound_message.event_type}: {inbound_message.content}"
        
        # Create conversation ID for memory
        conversation_id = f"{inbound_source}-{context.agent_id}"
        
        # Retrieve or initialize conversation memory
        chat_history = []
        if self._preserve_history and conversation_id in state.llamaindex_memory:
            memory = state.llamaindex_memory[conversation_id]
            chat_history = memory.get("chat_history", [])
            logger.debug(f"Using existing memory for conversation {conversation_id}: {memory}")
        
        # Execute the LlamaIndex agent with the input
        try:
            logger.debug(f"Running agent with input: {input_text}")
            
            # Check if the run method is a coroutine function (async)
            if asyncio.iscoroutinefunction(self._llamaindex_agent.run):
                # If it's async, we need to run it in an event loop
                logger.info("Agent.run is async, running in event loop")
                
                # Function to run in the event loop
                async def run_agent_async():
                    return await self._llamaindex_agent.run(input_text)
                
                # Create a new event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run the async function in the event loop
                response = loop.run_until_complete(run_agent_async())
            else:
                # If it's a regular function, just call it directly
                logger.info("Agent.run is synchronous")
                response = self._llamaindex_agent.run(input_text)
            
            logger.debug(f"Agent.run response: {response}")
                
            # Extract the response text based on agent type
            if self._is_function_agent():
                # For FunctionAgent, response should be the string
                agent_output = str(response)
                # Log tool calls if available
                if hasattr(response, "tool_calls") and response.tool_calls:
                    tool_calls_str = json.dumps(response.tool_calls, indent=2)
                    logger.debug(f"Tool calls: {tool_calls_str}")
                    # Use our callback for logging
                    callback_handler.on_agent_action({"tool": "function_tool", "input": tool_calls_str})
            elif hasattr(response, "response"):
                # For ReAct agent, response has a response property
                agent_output = response.response
            else:
                # Fallback for other response formats
                agent_output = str(response)
            
            # Log the output
            logger.info(f"Agent output: {agent_output}")
            callback_handler.on_agent_finish(agent_output)
            
            # If we're preserving history, update the memory
            if self._preserve_history:
                if conversation_id not in state.llamaindex_memory:
                    state.llamaindex_memory[conversation_id] = {}
                
                memory = state.llamaindex_memory[conversation_id]
                memory["chat_history"] = chat_history + [(input_text, agent_output)]
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
            logger.error(f"Error executing LlamaIndex agent: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Send error message (we already checked message_client is valid)
            error_message = Message(
                source=context.agent_id,
                destination=inbound_source,
                channel=inbound_channel,
                content=f"Sorry, I encountered an error: {str(e)}",
                event_type=EventType.MESSAGE,
            )
            context.message_client.send_message(error_message)
        
        return state 