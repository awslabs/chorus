import os
import sys
import threading
import time
import uuid
import signal
import logging
import multiprocessing
from multiprocessing import Process
from os import getpid
from typing import Dict, List, Optional, Any, Set, Union
import contextlib

from chorus.agents import Agent
from chorus.communication.message_service import DEFAULT_ROUTER_PORT
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.agent_status import AgentStatus
from chorus.data.channel import Channel
from chorus.data.team_info import TeamInfo
from chorus.environment.global_context import ChorusGlobalContext
from chorus.core.state import RunnerState
from chorus.teams import Team
from chorus.workspace.stop_conditions import MultiAgentStopCondition
from chorus.util.visual_debugger import VisualDebugger
from chorus.communication.zmq_protocol import MessageType, ZMQMessage
from chorus.data.dialog import Message

logger = logging.getLogger(__name__)

MAX_INSTNACE_LIMIT = 500

class Chorus(object):
    """Chorus runner that manages and coordinate multiple agents and teams in an orchestrated environment.

    This class serves as the main runner for coordinating agents and teams,
    managing their communication channels, and controlling their execution flow.

    Args:
        agents: List of individual agents to be managed by the chorus.
        teams: List of teams (groups of agents) to be managed by the chorus.
        channels: List of communication channels for agents/teams to interact.
        global_context: Global context object containing shared state and resources.
        simulator_state: State object tracking the status of all agents/teams.
        zmq_port: Port for ZMQ router socket.
        max_idle_time: Maximum time in seconds to wait while system is idle before stopping.
        tick_interval: Time in seconds between system update ticks.
        stop_conditions: List of conditions that will trigger the chorus to stop.
        debug: Whether to run in debug mode with additional logging.
        visual: Whether to enable visual debugging.
        visual_port: Port for the visual debugger.

    Raises:
        ValueError: If neither agents nor teams are specified, or if the total number
            of agents and teams exceeds MAX_INSTNACE_LIMIT.
    """

    def __init__(
        self,
        agents: Optional[List[Agent]] = None,
        teams: Optional[List[Team]] = None,
        channels: Optional[List[Channel]] = None,
        global_context: Optional[ChorusGlobalContext] = None,
        simulator_state: Optional[RunnerState] = None,
        zmq_port: int = DEFAULT_ROUTER_PORT,
        max_idle_time: int = 300,
        tick_interval: int = 1,
        stop_conditions: Optional[List[MultiAgentStopCondition]] = None,
        debug: bool = False,
        visual: bool = False,
        visual_port: int = 5000,
    ):
        """Initialize the runner with configuration.

        Args:
            agents (Optional[List[Agent]]): List of agents to be managed.
            teams (Optional[List[Team]]): List of teams to be managed.
            channels (Optional[List[Channel]]): List of channels to be managed.
            global_context (ChorusGlobalContext): Global context for the chorus.
            simulator_state (RunnerState): State of the simulator.
            zmq_port (int): Port for ZMQ router socket.
            max_idle_time (int): Maximum idle time before stopping.
            tick_interval (int): Interval between ticks.
            stop_conditions (Optional[List[MultiAgentStopCondition]]): List of stop conditions.
            debug (bool): Debug mode flag.
            visual (bool): Visual debugging flag.
            visual_port (int): Port for the visual debugger.
        """
        if not agents and not teams:
            raise ValueError("Either agents or teams need to be specified for launching the Chorus runner.")
        self._max_idle_time = max_idle_time
        self._tick_interval = tick_interval
        self._agents = agents if agents is not None else []
        self._teams = teams if teams is not None else []
        if len(self._agents) + len(self._teams) > MAX_INSTNACE_LIMIT:
            raise ValueError(f"The number of agents and teams exceeds the maximum limit: {MAX_INSTNACE_LIMIT}")
        self._agent_map: Dict = {}
        self._agent_team_map: Dict = {}
        self._team_info_map: Dict = {}  # Maps agent UUIDs to TeamInfo objects
        self._agent_processes: Dict[str, Process] = {}
        self._agent_states: Dict[str, Optional[AgentState]] = {}
        self._global_context = global_context
        self._is_busy = False
        self._last_busy_timestamp = int(time.time())
        self._debug = debug
        self._visual = visual
        self._visual_debugger = None
        self._chorus_thread = None
        self._logged_message_ids: set = set()  # Track which messages have been logged
        if self._visual:
            self._visual_debugger = VisualDebugger(port=visual_port)
            # Register teams and channels with the visual debugger
            if self._teams:
                for team in self._teams:
                    self._visual_debugger.add_team(team)
            if channels:
                for channel in channels:
                    self._visual_debugger.add_channel(channel)
        if self._global_context is None:
            self._global_context = ChorusGlobalContext(zmq_router_port=zmq_port)
        if channels is not None:
            for channel in channels:
                self._global_context.register_channel(channel)
        self._simulator_state = simulator_state
        if self._simulator_state is None:
            self._simulator_state = RunnerState()
        self._stop_conditions = stop_conditions
        if self._stop_conditions is None:
            self._stop_conditions = []
        for stopper in self._stop_conditions:
            stopper.set_runner(self)
        # Initialize agent contexts and states
        if self._agents:
            for agent in self._agents:
                self.register_agent(agent)
        if self._teams:
            for team in self._teams:
                self.register_agent(team)
                team_info = team.get_team_info()
                agent_ids = []
                for agent in team.get_agents():
                    agent_id = self.register_agent(agent, team_info=team_info)
                    agent_ids.append(agent_id)
                team_info.agent_ids = agent_ids
        self.register_signal_handler()
        self._stopping = False
        self._global_run_uuid = str(uuid.uuid4())[:8]
    
    def register_agent(self, agent: Agent, team_info: Optional[TeamInfo] = None) -> str:
        """Register an agent with the Chorus runner.
        
        Args:
            agent: The agent to register
            team_info: Optional team info if the agent belongs to a team
            
        Returns:
            The agent class UUID
        """
        # Get the agent's class UUID
        class_uuid = agent.get_agent_class_uuid()
        
        # Store agent in the agent map
        self._agent_map[class_uuid] = agent
        self._agent_states[class_uuid] = None
        
        # Update simulator state
        if self._simulator_state is not None:
            self._simulator_state.update_agent_state(class_uuid, None)
            
        # If this agent is part of a team, record that
        if team_info is not None:
            self._agent_team_map[class_uuid] = team_info.identifier
            # Store the team info for later transmission
            self._team_info_map[class_uuid] = team_info
            
        return class_uuid
    
    def spawn_agent_process(self, agent_uuid: str):
        """Spawn a new process for an agent.
        
        Args:
            agent_uuid: Class UUID of the agent to spawn
            
        Returns:
            The spawned process
        """
        agent = self._agent_map[agent_uuid]
        state = self._agent_states[agent_uuid]
        
        # Create a process for the agent
        proc = Process(
            target=Chorus.run_agent,
            args=(agent, state, self._global_context.zmq_router_port)
        )
        
        # Store the process
        self._agent_processes[agent_uuid] = proc
        
        # Start the process
        proc.start()
        
        return proc
    
    @staticmethod
    def run_agent(agent: Agent, state: Optional[AgentState], zmq_port: int):
        """Run an agent in a new process.
        
        Args:
            agent: The agent to run
            state: Optional state for the agent
            zmq_port: Port for the ZMQ router
        """
        # Initialize the agent with its saved args
        agent.initialize()
        
        # Initialize context and state
        context = agent.init_context()
        agent_id = context.agent_id
        if state is None:
            state = agent.init_state()
        
        try:
            # Run the agent
            agent.run(router_port=zmq_port, context=context, state=state)
        except Exception as e:
            import traceback
            error_msg = f"\n{'='*60}\nERROR: Agent {agent_id} crashed with exception:\n"
            error_msg += f"\nException Type: {type(e).__name__}"
            error_msg += f"\nException Message: {str(e)}"
            error_msg += f"\n\nFull Traceback:\n{traceback.format_exc()}"
            error_msg += f"\n{'='*60}\n"
            print(error_msg)

    def send_team_info_to_agent(self, agent_id: str, team_info: TeamInfo):
        """Send team information to an agent.
        
        Args:
            agent_id: The agent ID to send team info to
            team_info: The TeamInfo object to send
        """
        if self._global_context and hasattr(self._global_context, '_message_router'):
            team_info_dict = team_info.model_dump()
            self._global_context._message_router.send_team_info(agent_id, team_info_dict)
            logger.info(f"Sent team info for team {team_info.name} to agent {agent_id}")
        else:
            logger.warning(f"Could not send team info to agent {agent_id}: no message router available")

    def run(self):
        """Execute the main running loop for agent collaboration and block the thread.

        Manages the lifecycle of agents, coordinates their interactions, and handles
        any errors or exceptions that occur during execution.

        Returns:
            Dict: Results of the execution including agent outputs and final state.

        Raises:
            RunnerError: If there is an error during execution.
        """
        self._is_busy = True
        self._last_busy_timestamp = int(time.time())
        
        # Set to track agents we've already sent team info to
        team_info_sent = set()

        # Start visual debugger if enabled
        if self._visual and self._visual_debugger:
            self._visual_debugger.start()
            # Register all agent states
            for agent_uuid in self._agent_map.keys():
                # Register agent states
                state = self._simulator_state.get_agent_state(agent_uuid)
                if state:
                    self._visual_debugger.register_state(agent_uuid, state)

        try:
            # Start all agent processes
            for agent_uuid in self._agent_map.keys():
                self.spawn_agent_process(agent_uuid)
                
            # Monitor agent processes
            while True:
                # Check if any processes have terminated
                for agent_uuid, proc in list(self._agent_processes.items()):
                    if not proc.is_alive():
                        exitcode = proc.exitcode
                        logger.info(f"Agent {agent_uuid} process terminated with exit code {exitcode}")
                        
                        # Remove from active processes
                        del self._agent_processes[agent_uuid]
                        
                        # Respawn if unexpectedly terminated
                        if exitcode != 0 and not self._stopping:
                            logger.warning(f"Agent {agent_uuid} process terminated unexpectedly, respawning")
                            self.spawn_agent_process(agent_uuid)
                
                # Send team info to newly connected agents
                if self._global_context and hasattr(self._global_context, '_message_router'):
                    router = self._global_context._message_router
                    for agent_uuid, team_info in self._team_info_map.items():
                        if agent_uuid not in team_info_sent:
                            # Get the actual agent ID that the agent registered with (context ID)
                            agent = self._agent_map[agent_uuid]
                            agent_id = agent.identifier()
                            
                            # Check if this agent has connected to the router
                            if agent_id in router._agent_identities:
                                # Send team info to the agent
                                self.send_team_info_to_agent(agent_id, team_info)
                                team_info_sent.add(agent_uuid)
                
                # Update the visual debugger with latest messages
                if self._visual and self._visual_debugger:
                    # Track new messages
                    new_messages = []
                    for msg in self._global_context.fetch_all_messages():
                        if msg.message_id not in self._logged_message_ids:
                            new_messages.append(msg)
                            self._logged_message_ids.add(msg.message_id)
                
                # Check stop conditions
                ending = False
                if self._stopping:
                    logger.info("Chorus is stopping...")
                    break
                for stopper in self._stop_conditions:
                    if stopper.stop():
                        logger.info(f"Simulator stopped due to {str(stopper)}")
                        ending = True
                        break
                if ending:
                    break
                    
                # Check if all processes have terminated
                if not self._agent_processes:
                    logger.info("All agent processes have terminated")
                    break
                    
                # Sleep to avoid busy waiting
                time.sleep(self._tick_interval)
        finally:
            # Stop all agent processes
            self.stop_all_agents()
            self._is_busy = False
            
            # Shutdown global context
            if self._global_context:
                self._global_context.shutdown()

    def stop_all_agents(self):
        """Stop all running agent processes."""
        # Send stop signals to all agents
        if self._global_context:
            for agent_uuid in list(self._agent_processes.keys()):
                try:
                    self._global_context.stop_agent(agent_uuid)
                    logger.info(f"Sent stop signal to agent {agent_uuid}")
                except Exception as e:
                    logger.warning(f"Error sending stop signal to agent {agent_uuid}: {e}")
                
        # Wait for processes to terminate gracefully
        grace_period = 5  # seconds to wait for graceful termination
        deadline = time.time() + grace_period
        while self._agent_processes and time.time() < deadline:
            for agent_uuid, proc in list(self._agent_processes.items()):
                try:
                    if not proc.is_alive():
                        logger.info(f"Agent {agent_uuid} process terminated gracefully")
                        del self._agent_processes[agent_uuid]
                except Exception as e:
                    logger.warning(f"Error checking if agent {agent_uuid} process is alive: {e}")
                    # Remove from tracked processes to avoid further issues
                    self._agent_processes.pop(agent_uuid, None)
            time.sleep(0.1)
            
        # Forcefully terminate any remaining processes
        for agent_uuid, proc in list(self._agent_processes.items()):
            try:
                logger.warning(f"Forcefully terminating agent {agent_uuid} process")
                proc.terminate()
                proc.join(timeout=1.0)
            except Exception as e:
                logger.error(f"Error terminating agent {agent_uuid} process: {e}")
            finally:
                # Always remove from our tracked processes
                self._agent_processes.pop(agent_uuid, None)

    def is_busy(self):
        return self._is_busy

    def get_environment(self) -> Optional[ChorusGlobalContext]:
        return self._global_context
    
    def get_global_context(self) -> Optional[ChorusGlobalContext]:
        return self._global_context
    
    def get_global_state(self) -> Optional[RunnerState]:
        return self._simulator_state
    
    def get_agent_context(self, agent_id: str) -> Optional[AgentContext]:
        raise NotImplementedError
    
    def get_agent_state(self, agent_uuid: str) -> Optional[AgentState]:
        """Get the current state of an agent.
        
        Args:
            agent_uuid: UUID of the agent whose state to retrieve
            
        Returns:
            The agent's state if found, None otherwise
        """
        if agent_uuid in self._agent_states:
            return self._agent_states[agent_uuid]
        return None

    def dump_environment_state(self):
        pass

    def get_agents_status(self) -> Dict[str, AgentStatus]:
        """Get the status of all agents.
        
        Returns:
            Dictionary mapping agent UUIDs to their current status
        """
        agent_status_map = {}
        for agent_uuid in self._agent_map.keys():
            if agent_uuid in self._agent_processes and self._agent_processes[agent_uuid].is_alive():
                agent_status_map[agent_uuid] = AgentStatus.BUSY
            else:
                agent_status_map[agent_uuid] = AgentStatus.AVAILABLE
                
        # Update with status from status manager if available
        if self._global_context:
            sm = self._global_context.status_manager()
            for agent_uuid in self._agent_map.keys():
                status = sm.get_status(agent_uuid)
                if status is not None:
                    agent_status_map[agent_uuid] = status
                    
        return agent_status_map

    def get_last_activity_timestamp(self) -> Optional[int]:
        """Get the timestamp of the last activity in the chorus.

        Returns:
            Optional[int]: The Unix timestamp of the last activity.
        """
        if self._global_context is None:
            return None
        sm = self._global_context.status_manager()
        records = sm.get_records()
        if records:
            last_timestamp, _, _ = records[-1]
            return max(self._last_busy_timestamp, last_timestamp)
        else:
            return self._last_busy_timestamp

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def start(self):
        """
        Start Chorus in a new thread and wait until all agents are connected to the router.
        
        This method starts the Chorus system in a background thread and blocks until all
        agents have successfully connected to the ZMQ router and registered themselves.
        This ensures that when this method returns, the entire system is properly initialized
        and ready to handle messages.
        """
        if self._chorus_thread and self._chorus_thread.is_alive():
            return
        
        # Start the chorus thread
        self._chorus_thread = threading.Thread(target=self.run)
        self._chorus_thread.start()
        
        # Wait for the thread to initialize
        time.sleep(0.5)
        
        # The maximum time to wait for all agents to connect (in seconds)
        max_wait_time = 30
        polling_interval = 0.5
        start_time = time.time()
        
        # Get the expected agent IDs
        expected_agent_ids = {agent.identifier() for agent_uuid, agent in self._agent_map.items()}
        total_agents = len(expected_agent_ids)
        
        logger.info(f"Waiting for {total_agents} agents to connect to the router...")
        last_registered_count = 0
        
        while time.time() - start_time < max_wait_time:
            # Check if the global context is tracking registrations
            if hasattr(self._global_context, '_registered_agents'):
                registered_count = len(self._global_context._registered_agents)
                
                # Log progress only when the count changes
                if registered_count > last_registered_count:
                    logger.info(f"Progress: {registered_count}/{total_agents} agents connected")
                    last_registered_count = registered_count
                
                # Check if all expected agents are registered
                if self._global_context._registered_agents.issuperset(expected_agent_ids):
                    logger.info(f"All {total_agents} agents successfully connected and registered")
                    return
            
            # Sleep to avoid busy waiting
            time.sleep(polling_interval)
        
        # If we're here, we timed out
        if hasattr(self._global_context, '_registered_agents'):
            registered_count = len(self._global_context._registered_agents)
            missing_agents = expected_agent_ids - self._global_context._registered_agents
            logger.warning(f"Timed out waiting for all agents to connect. {registered_count}/{total_agents} agents connected.")
            if missing_agents:
                logger.warning(f"Missing agents: {', '.join(missing_agents)}")
        else:
            logger.warning(f"Timed out waiting for agents to connect. Registration tracking not available.")
        # Continue anyway, as agents might still connect later
    
    def stop(self):
        """Stop Chorus and wait for it to finish.
        
        This method sets the stopping flag and waits for the chorus thread to complete
        if it exists and is running. This ensures a clean shutdown of all running processes.
        """
        self._stopping = True
        if self._chorus_thread and self._chorus_thread.is_alive():
            self._chorus_thread.join()
        self._stopping = False
    
    def cleanup(self, *args, **kwargs):
        """Clean up chorus resources and terminate all processes.
        
        This method is called when receiving SIGINT or SIGTERM signals. It terminates
        all running processes and exits the program.

        Args:
            *args: Variable length argument list for signal handler compatibility.
            **kwargs: Arbitrary keyword arguments for signal handler compatibility.
        """
        print("")
        print("Chorus is terminating...")
        
        # Stop all agent processes
        self.stop_all_agents()
        
        # Shutdown global context
        if self._global_context:
            self._global_context.shutdown()
        sys.exit(0)
            
    def send_message(
        self, 
        message: Union[Message, str, dict], 
        destination: Optional[str] = None, 
        channel: Optional[str] = None, 
        source: Optional[str] = None
    ):
        """Send a message to an agent.
        
        Args:
            destination: The ID of the agent to send the message to
            message: The content of the message to send
            channel: Optional channel to use for the message
            source: Optional source ID, defaults to the human identifier
            
        Returns:
            The sent message
        """
        if self._global_context is None:
            logger.error("Cannot send message: global context is None")
            return None
            
        if source is None:
            source = self._global_context.human_identifier
            
        if isinstance(message, str):
            message = Message(
                source=source,
                destination=destination,
                channel=channel,
                content=message
            )
        elif isinstance(message, dict):
            content = message.get("content", None)
            artifacts = message.copy()
            if "content" in artifacts:
                artifacts.pop("content")
            message = Message(
                source=source,
                destination=destination,
                channel=channel,
                content=content,
                artifacts=artifacts
            )
        # Send the message
        self._global_context.send_message(message)
        
    def wait_for_response(
        self,
        source: str,
        destination: Optional[str] = None,
        channel: Optional[str] = None,
        timeout: int = 300
    ) -> Optional[Message]:
        """Wait for a response from an agent.
        
        Args:
            source: The ID of the agent to wait for a response from
            destination: Optional destination ID, defaults to the human identifier
            channel: Optional channel to wait for a response on
            timeout: Maximum time to wait for a response in seconds
            
        Returns:
            The response message received, or None if no response was received
        """
        if self._global_context is None:
            logger.error("Cannot wait for response: global context is None")
            return None
            
        if destination is None:
            destination = self._global_context.human_identifier
            
        # Track message IDs we've already seen to avoid returning old messages
        message_history = self._global_context.filter_messages(
            source=source, destination=destination, channel=channel
        )
        seen_message_ids = {msg.message_id for msg in message_history}
        
        
        start_time = time.time()
        progress_interval = 10  # Print progress message every 10 seconds
        next_progress = start_time + progress_interval
        
        # Create direct reference to global context for more direct access
        ctx = self._global_context
        
        while time.time() - start_time < timeout:
            current_time = time.time()
            
            # Print progress message periodically
            if current_time >= next_progress:
                
                next_progress = current_time + progress_interval
                
                # Check if the agent is still running by requesting its state
                ctx.request_agent_state(source)
            
            # Direct access to all messages
            all_current_messages = ctx.fetch_all_messages()
            
            # Check for any message from source to destination
            for msg in all_current_messages:
                if (msg.source == source and 
                    msg.destination == destination and 
                    msg.message_id not in seen_message_ids):
                    return msg
                    
            # Sleep to avoid high CPU usage
            time.sleep(0.5)
            
        logger.warning(f"No response received from {source} after {timeout} seconds")
        
        # Final check - maybe the message was processed but we missed it somehow
        latest_messages = ctx.filter_messages(source=source, destination=destination, channel=channel)
        for msg in latest_messages:
            if msg.message_id not in seen_message_ids:
                return msg
                
        return None
        
    def send_and_wait(
        self, 
        destination: str, 
        message: str, 
        channel: Optional[str] = None, 
        source: Optional[str] = None,
        timeout: int = 300
    ) -> Optional[Message]:
        """Send a message to an agent and wait for a response.
        
        Args:
            destination: The ID of the agent to send the message to
            message: The content of the message to send
            channel: Optional channel to use for the message
            source: Optional source ID, defaults to the human identifier
            timeout: Maximum time to wait for a response in seconds
            
        Returns:
            The response message received, or None if no response was received
        """
        if self._global_context is None:
            logger.error("Cannot send message: global context is None")
            return None
            
        if source is None:
            source = self._global_context.human_identifier
        
            
        # Send the message
        self.send_message(destination=destination, message=message, channel=channel, source=source)
        
        
        # Give some time for the message to propagate and the agent to process it
        time.sleep(1)
        
        # Wait for response with timeout
        return self.wait_for_response(source=destination, destination=source, channel=channel, timeout=timeout)
