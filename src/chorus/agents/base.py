from abc import ABCMeta
from abc import abstractmethod
import logging
import signal
import sys
import time
from typing import Dict, Optional, Any

from chorus.agents.meta import AgentMeta
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.communication.message_service import ChorusMessageClient

logger = logging.getLogger(__name__)

class Agent(AgentMeta):
    """Base class for all agents in the Chorus framework.

    This abstract class defines the core interface that all agents must implement.
    It provides basic initialization methods and requires implementing an iterate method
    for the agent's main processing loop.
    """

    def __init__(self):
        """Initialize a new agent.
        """
        self._initialized = True
        self._running = False
        self._comm_client = None

    def init_context(self) -> AgentContext:
        """Initialize the agent's context.

        Creates a new AgentContext instance with a unique ID for this agent.

        Returns:
            AgentContext: A new context object for this agent.
        """
        return AgentContext(agent_id=self.identifier())

    def init_state(self) -> AgentState:
        """Initialize the agent's state.

        Creates a new AgentState instance with default values.

        Returns:
            AgentState: A new state object for this agent.
        """
        return AgentState()

    @abstractmethod
    def iterate(self, context: AgentContext, state: AgentState) -> AgentState:
        """Execute one iteration of the agent's processing loop.

        Args:
            context: The agent's context containing environmental information.
            state: The current state of the agent.

        Returns:
            AgentState: The updated agent state after processing.
        """
        pass
    
    def run(self, router_host: str = "localhost", router_port: int = 5555, 
            context: Optional[AgentContext] = None, state: Optional[AgentState] = None):
        """Run the agent in a continuous loop, connecting to the ZMQ router.
        
        This method should be called in a subprocess. It initializes a ZMQ client
        for the agent, connects to the router, and then enters a main loop that
        processes messages and periodically runs the agent's iterate method.
        
        Args:
            router_host: Hostname of the ZMQ router
            router_port: Port of the ZMQ router
            context: Initial context for the agent, or None to initialize
            state: Initial state for the agent, or None to initialize
        """
        # Setup signal handler for clean shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        # Initialize context and state if not provided
        if context is None:
            context = self.init_context()
        if state is None:
            state = self.init_state()
            
        agent_id = context.agent_id
            
        # Initialize ZMQ client
        self._comm_client = ChorusMessageClient(agent_id, router_host, router_port)
        
        # Set the agent's message service to the ZMQ client directly
        context.set_message_client(self._comm_client)
        
        # Start message client thread
        self._comm_client.start()
        self._running = True
        
        # Give the client time to register and receive initial messages
        time.sleep(0.5)
        
        # Check if team info was received and update context
        team_info_dict = self._comm_client.get_team_info()
        if team_info_dict:
            from chorus.data.team_info import TeamInfo
            team_info = TeamInfo.model_validate(team_info_dict)
            context.team_info = team_info
            logger.info(f"Agent {agent_id} updated with team info for team {team_info.name}")
        
        logger.info(f"Agent {agent_id} started")
        
        try:
            # Main agent loop
            iteration_count = 0
            while self._running and self._comm_client._running:
                # Run one iteration of the agent's logic
                try:
                    new_state = self.iterate(context, state)
                    state = new_state
                    
                    # Send state update to router
                    self._comm_client.send_state_update(state.model_dump())
                    iteration_count += 1
                except Exception as e:
                    logger.error(f"Error in agent {agent_id} iteration: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # Sleep to avoid busy waiting
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info(f"Agent {agent_id} received keyboard interrupt")
        except Exception as e:
            logger.error(f"Agent {agent_id} error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # Clean up
            logger.info(f"Agent {agent_id} shutting down")
            if self._comm_client:
                self._comm_client.send_stop_ack()
                self._comm_client.stop()
    
    def _handle_signal(self, signum, frame):
        """Handle signals for clean shutdown."""
        logger.info(f"Agent {self.identifier()} received signal {signum}")
        self._running = False
        if self._comm_client:
            self._comm_client.send_stop_ack()
            self._comm_client.stop()
        sys.exit(0)
