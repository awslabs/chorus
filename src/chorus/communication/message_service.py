import json
import logging
import threading
import time
import uuid
import zmq
import random
from typing import Dict, List, Optional, Set, ClassVar

from pydantic import BaseModel, Field

from chorus.data.dialog import Message
from chorus.communication.zmq_protocol import MessageType, ZMQMessage

logger = logging.getLogger(__name__)

# ZMQ port configurations
DEFAULT_ROUTER_PORT = 5555
ROUTER_IDENTITY = b"ROUTER"

class ChorusMessageRouter:
    """
    ZMQ-based message router for Chorus agents.
    
    This replaces the previous MessageService based on multiprocessing.Manager.
    It acts as a centralized router that agents connect to as dealers.
    """
    
    def __init__(self, port: int = DEFAULT_ROUTER_PORT, max_retry: int = 5):
        """Initialize the ZMQ message router.
        
        Args:
            port: Port number for the ZMQ router socket
            max_retry: Maximum number of retries for binding to a port
        """
        self.port = port
        
        self._zmq_context = zmq.Context()
        self._router_socket = self._zmq_context.socket(zmq.ROUTER)
        self._router_socket.identity = ROUTER_IDENTITY
        
        # Try to bind to the specified port
        port_bound = False
        retries = 0
        
        while not port_bound and retries < max_retry:
            try:
                self._router_socket.bind(f"tcp://*:{self.port}")
                port_bound = True
                logger.info(f"ZMQ router bound to port {self.port}")
            except zmq.error.ZMQError as e:
                if "Address already in use" in str(e) and retries < max_retry - 1:
                    old_port = self.port
                    self.port = random.randint(10000, 65535)
                    logger.warning(f"Port {old_port} already in use, trying port {self.port}")
                    retries += 1
                else:
                    logger.error(f"Failed to bind ZMQ router to port after {retries} retries: {e}")
                    raise
        
        self._message_history = []
        self._running = False
        self._thread = None
        self._agent_identities = {}
        self._global_message_ids = set()
        
    def start(self):
        """Start the message router in a background thread."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._router_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the message router thread."""
        if not self._running:
            return
            
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        # Send STOP signal to all connected agents
        for agent_id, identity in list(self._agent_identities.items()):
            try:
                self._send_to_agent(identity, ZMQMessage(
                    msg_type=MessageType.STOP,
                    agent_id=agent_id
                ))
            except Exception as e:
                logger.warning(f"Error sending stop signal to agent {agent_id}: {e}")
        
        # Close socket and terminate context
        try:    
            self._router_socket.close(linger=1000)  # Allow 1 second for messages to be sent
            time.sleep(0.2)  # Give a moment for socket operations to complete
            self._zmq_context.term()
            logger.info(f"ZMQ router on port {self.port} successfully shut down")
        except Exception as e:
            logger.error(f"Error during ZMQ router shutdown: {e}")
    
    def _router_loop(self):
        """Main router event loop processing messages from agents."""
        while self._running:
            try:
                # Use poll with timeout to allow checking _running flag
                if not self._router_socket.poll(timeout=100):
                    continue
                    
                # Receive message: [identity, empty, message]
                identity, empty, message_data = self._router_socket.recv_multipart()
                
                # Process the message
                self._process_message(identity, message_data)
                
            except Exception as e:
                logger.error(f"Error in router loop: {e}")
                
    def _process_message(self, identity: bytes, message_data: bytes):
        """Process a message received from an agent.
        
        Args:
            identity: ZMQ identity of the sending agent
            message_data: Raw message data
        """
        try:
            zmq_message = ZMQMessage.from_json(message_data.decode('utf-8'))
            msg_type = zmq_message.msg_type
            agent_id = zmq_message.agent_id
            
            # Store agent identity mapping
            if agent_id and agent_id not in self._agent_identities:
                self._agent_identities[agent_id] = identity
            
            # Handle the message based on type
            if msg_type == MessageType.REGISTER:
                # Agent registration
                self._handle_register(identity, zmq_message)
            elif msg_type == MessageType.AGENT_MESSAGE:
                # Regular agent message for the global pool
                self._handle_agent_message(identity, zmq_message)
            elif msg_type == MessageType.STATE_UPDATE:
                # Agent is reporting its state
                self._handle_state_update(identity, zmq_message)
            elif msg_type == MessageType.HEARTBEAT:
                # Heartbeat response
                self._send_to_agent(identity, ZMQMessage(
                    msg_type=MessageType.HEARTBEAT_ACK,
                    agent_id=agent_id
                ))
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def _handle_register(self, identity: bytes, zmq_message: ZMQMessage):
        """Handle agent registration message.
        
        Args:
            identity: ZMQ identity of the agent
            zmq_message: Registration message with agent info
        """
        agent_id = zmq_message.agent_id
        self._agent_identities[agent_id] = identity
        
        # Send acknowledgment
        self._send_to_agent(identity, ZMQMessage(
            msg_type=MessageType.REGISTER_ACK,
            agent_id=agent_id
        ))
        
        # If this agent has associated team info, send it
        # This will be handled by the outer context, which should call send_team_info
        
    def send_team_info(self, agent_id: str, team_info_dict: Dict):
        """Send team information to an agent.
        
        Args:
            agent_id: ID of the agent to send team info to
            team_info_dict: Dictionary representation of TeamInfo
        """
        if agent_id in self._agent_identities:
            identity = self._agent_identities[agent_id]
            self._send_to_agent(identity, ZMQMessage(
                msg_type=MessageType.TEAM_INFO,
                agent_id=agent_id,
                payload={"team_info": team_info_dict}
            ))
            logger.info(f"Sent team info to agent {agent_id}")

    def _handle_agent_message(self, identity: bytes, zmq_message: ZMQMessage):
        """Handle an agent message for the global message pool.
        
        Args:
            identity: ZMQ identity of the agent
            zmq_message: Message containing a chorus Message object
        """
        payload = zmq_message.payload
        if "message" not in payload:
            logger.error("Agent message without message payload")
            return
            
        message_dict = payload["message"]
        message = Message.model_validate(message_dict)
        
        # Add to global message history
        if message.message_id not in self._global_message_ids:
            self._message_history.append(message)
            self._global_message_ids.add(message.message_id)
            
            logger.info(f"ROUTER: Received message from {message.source} to {message.destination} on channel {message.channel}")
            
            # Special handling for messages destined for "human" - ensure they're stored
            if message.destination == "human":
                # No need to forward to human, it'll be picked up from global history
                return
            
            # Broadcast to other relevant agents
            for target_agent_id, target_identity in self._agent_identities.items():
                if target_agent_id != zmq_message.agent_id:
                    # Check if this agent should receive the message
                    if (message.destination == target_agent_id or 
                        (message.channel is not None and self._is_agent_in_channel(target_agent_id, message.channel))):
                        self._send_to_agent(target_identity, ZMQMessage(
                            msg_type=MessageType.ROUTER_MESSAGE,
                            agent_id=target_agent_id,
                            payload={"message": message_dict}
                        ))
                        
    def _handle_state_update(self, identity: bytes, zmq_message: ZMQMessage):
        """Handle agent state update message.
        
        Args:
            identity: ZMQ identity of the agent
            zmq_message: Message containing the agent's state
        """
        # This is handled at the router level (Chorus class)
        # The router needs to update the agent's state in its RunnerState
        pass
    
    def _send_to_agent(self, identity: bytes, zmq_message: ZMQMessage):
        """Send a ZMQ message to an agent.
        
        Args:
            identity: ZMQ identity of the target agent
            zmq_message: Message to send
        """
        try:
            message_data = zmq_message.to_json().encode('utf-8')
            self._router_socket.send_multipart([identity, b"", message_data])
        except Exception as e:
            logger.error(f"Error sending message to agent: {e}")
    
    def send_message(self, message: Message):
        """Send a message to the global message pool.
        
        Args:
            message: Message to send
        """
        if message.message_id is None:
            message.message_id = str(uuid.uuid4().hex)
            
        # Add to local message history
        if message.message_id not in self._global_message_ids:
            self._message_history.append(message)
            self._global_message_ids.add(message.message_id)
            
        # Broadcast to relevant agents
        message_dict = message.model_dump()
        
        # Send to specific agent if destination is specified
        if message.destination in self._agent_identities:
            identity = self._agent_identities[message.destination]
            self._send_to_agent(identity, ZMQMessage(
                msg_type=MessageType.ROUTER_MESSAGE,
                agent_id=message.destination,
                payload={"message": message_dict}
            ))
        
        # Broadcast to channel members if channel is specified
        if message.channel:
            for agent_id, identity in self._agent_identities.items():
                if self._is_agent_in_channel(agent_id, message.channel):
                    self._send_to_agent(identity, ZMQMessage(
                        msg_type=MessageType.ROUTER_MESSAGE,
                        agent_id=agent_id,
                        payload={"message": message_dict}
                    ))
    
    def fetch_all_messages(self) -> List[Message]:
        """Fetch all messages in the global pool.
        
        Returns:
            List of all messages
        """
        return self._message_history
    
    def filter_messages(self, source: Optional[str] = None, destination: Optional[str] = None, 
                        channel: Optional[str] = None) -> List[Message]:
        """Filter messages based on criteria.
        
        Args:
            source: Optional source agent ID
            destination: Optional destination agent ID
            channel: Optional channel name
            
        Returns:
            List of filtered messages
        """
        return [
            msg for msg in self._message_history
            if (source is None or msg.source == source)
            and (destination is None or msg.destination == destination)
            and (channel is None or msg.channel == channel)
        ]
    
    def request_agent_state(self, agent_id: str):
        """Request the current state from an agent.
        
        Args:
            agent_id: ID of the agent
        """
        if agent_id in self._agent_identities:
            identity = self._agent_identities[agent_id]
            self._send_to_agent(identity, ZMQMessage(
                msg_type=MessageType.DUMP_STATE,
                agent_id=agent_id
            ))
    
    def stop_agent(self, agent_id: str):
        """Send a stop signal to an agent.
        
        Args:
            agent_id: ID of the agent
        """
        if agent_id in self._agent_identities:
            identity = self._agent_identities[agent_id]
            self._send_to_agent(identity, ZMQMessage(
                msg_type=MessageType.STOP,
                agent_id=agent_id
            ))
    
    def _is_agent_in_channel(self, agent_id: str, channel: str) -> bool:
        """Check if an agent is a member of a channel.
        
        This is implemented at the ChorusGlobalContext level, so we'll
        rely on the router owner to determine channel membership.
        
        Args:
            agent_id: Agent ID to check
            channel: Channel name
            
        Returns:
            True if agent is in channel, False otherwise
        """
        # This is a stub - actual implementation needs channel info from global context
        return True  # Default to True for simple routing


class ChorusMessageClient:
    """
    ZMQ-based message client for Chorus agents.
    
    This replaces the previous MessageService based on multiprocessing.Manager.
    Each agent creates a client that connects to the central router.
    """
    
    def __init__(self, agent_id: str, router_host: str = "localhost", 
                 router_port: int = DEFAULT_ROUTER_PORT):
        """Initialize the ZMQ message client.
        
        Args:
            agent_id: ID of the agent this client belongs to
            router_host: Hostname of the ZMQ router
            router_port: Port number of the ZMQ router
        """
        self.agent_id = agent_id
        
        self._zmq_context = zmq.Context()
        self._dealer_socket = self._zmq_context.socket(zmq.DEALER)
        self._dealer_socket.identity = agent_id.encode('utf-8')
        self._dealer_socket.connect(f"tcp://{router_host}:{router_port}")
        
        self._message_history = []
        self._local_message_ids = set()
        self._running = False
        self._thread = None
        self._team_info = None
        
        # Register with the router
        self._register()
        
    def _register(self):
        """Register this client with the router."""
        register_msg = ZMQMessage(
            msg_type=MessageType.REGISTER,
            agent_id=self.agent_id
        )
        self._send_to_router(register_msg)
        
    def start(self):
        """Start the message client in a background thread."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._client_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the message client thread."""
        if not self._running:
            return
            
        self._running = False
        
        # Try to send a stop acknowledgment before shutting down
        try:
            self.send_stop_ack()
        except Exception as e:
            logger.warning(f"Error sending stop acknowledgment: {e}")
        
        # Wait for the client thread to terminate
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
            
        # Properly close sockets and terminate context
        try:
            self._dealer_socket.close(linger=500)  # 500ms linger time
            time.sleep(0.1)  # Brief pause for socket ops to complete
            self._zmq_context.term()
            logger.info(f"ZMQ client for agent {self.agent_id} successfully shut down")
        except Exception as e:
            logger.error(f"Error during ZMQ client shutdown: {e}")
    
    def _client_loop(self):
        """Main client event loop processing messages from the router."""
        while self._running:
            try:
                # Use poll with timeout to allow checking _running flag
                if not self._dealer_socket.poll(timeout=100):
                    continue
                    
                # Receive message: [empty, message]
                empty, message_data = self._dealer_socket.recv_multipart()
                
                # Process the message
                self._process_message(message_data)
                
            except Exception as e:
                logger.error(f"Error in client loop: {e}")
                
    def _process_message(self, message_data: bytes):
        """Process a message received from the router.
        
        Args:
            message_data: Raw message data
        """
        try:
            zmq_message = ZMQMessage.from_json(message_data.decode('utf-8'))
            msg_type = zmq_message.msg_type
            
            # Handle the message based on type
            if msg_type == MessageType.REGISTER_ACK:
                # Registration acknowledgment
                logger.debug(f"Agent {self.agent_id} registered with router")
            elif msg_type == MessageType.ROUTER_MESSAGE:
                # Regular message from the router
                self._handle_router_message(zmq_message)
            elif msg_type == MessageType.TEAM_INFO:
                # Team info for this agent
                self._handle_team_info(zmq_message)
            elif msg_type == MessageType.GET_STATE:
                # Router is requesting agent state
                self._handle_get_state(zmq_message)
            elif msg_type == MessageType.STOP:
                # Router is requesting agent to stop
                self._running = False
                # The agent process should check this and exit
            elif msg_type == MessageType.HEARTBEAT:
                # Heartbeat request
                self._send_to_router(ZMQMessage(
                    msg_type=MessageType.HEARTBEAT_ACK,
                    agent_id=self.agent_id
                ))
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def _handle_router_message(self, zmq_message: ZMQMessage):
        """Handle a message from the router.
        
        Args:
            zmq_message: Message from the router
        """
        payload = zmq_message.payload
        if "message" not in payload:
            logger.error("Router message without message payload")
            return
            
        message_dict = payload["message"]
        message = Message.model_validate(message_dict)
        
        
        # Add to local message history if not already present
        if message.message_id not in self._local_message_ids:
            self._message_history.append(message)
            self._local_message_ids.add(message.message_id)
            
    def _handle_team_info(self, zmq_message: ZMQMessage):
        """Handle team info message from the router.
        
        This is stored in the client to be accessed by the agent.
        
        Args:
            zmq_message: Team info message
        """
        payload = zmq_message.payload
        if "team_info" not in payload:
            logger.error("Team info message without team_info payload")
            return
        
        # Store the team info for later retrieval by the agent
        self._team_info = payload["team_info"]
        logger.info(f"Agent {self.agent_id} received team info")
    
    def _handle_get_state(self, zmq_message: ZMQMessage):
        """Handle a request for agent state.
        
        Args:
            zmq_message: State request message
        """
        # This is handled at the agent level
        # The agent needs to send its state back to the router
        pass
    
    def _send_to_router(self, zmq_message: ZMQMessage):
        """Send a ZMQ message to the router.
        
        Args:
            zmq_message: Message to send
        """
        try:
            message_data = zmq_message.to_json().encode('utf-8')
            self._dealer_socket.send_multipart([b"", message_data])
        except Exception as e:
            if "Socket operation on non-socket" not in str(e):
                logger.error(f"Error sending message to router: {e}")
    
    def send_message(self, message: Message):
        """Send a message through the router.
        
        Args:
            message: Message to send
        """
        
        if message.message_id is None:
            message.message_id = str(uuid.uuid4().hex)
            
        # Add to local message history
        if message.message_id not in self._local_message_ids:
            self._message_history.append(message)
            self._local_message_ids.add(message.message_id)
            
        # Send to router
        message_dict = message.model_dump()
        try:
            self._send_to_router(ZMQMessage(
                msg_type=MessageType.AGENT_MESSAGE,
                agent_id=self.agent_id,
                payload={"message": message_dict}
            ))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    def fetch_all_messages(self) -> List[Message]:
        """Fetch all messages in the local message history.
        
        Returns:
            List of all messages
        """
        return self._message_history
    
    def filter_messages(self, source: Optional[str] = None, destination: Optional[str] = None, 
                        channel: Optional[str] = None) -> List[Message]:
        """Filter messages based on criteria.
        
        Args:
            source: Optional source agent ID
            destination: Optional destination agent ID
            channel: Optional channel name
            
        Returns:
            List of filtered messages
        """
        return [
            msg for msg in self._message_history
            if (source is None or msg.source == source)
            and (destination is None or msg.destination == destination)
            and (channel is None or msg.channel == channel)
        ]
    
    def send_state_update(self, state_dict: Dict):
        """Send agent state update to the router.
        
        Args:
            state_dict: Dictionary representation of agent state
        """
        # Handle JSON serialization of set objects
        def set_handler(obj):
            if isinstance(obj, set):
                return list(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
        # Convert state_dict to JSON-safe dictionary
        try:
            json_str = json.dumps(state_dict, default=set_handler)
            json_safe_dict = json.loads(json_str)
            
            self._send_to_router(ZMQMessage(
                msg_type=MessageType.STATE_UPDATE,
                agent_id=self.agent_id,
                payload={"state": json_safe_dict}
            ))
        except Exception as e:
            logger.error(f"Error sending state update: {e}")
    
    def send_stop_ack(self):
        """Send acknowledgment of stop request to the router."""
        self._send_to_router(ZMQMessage(
            msg_type=MessageType.STOP_ACK,
            agent_id=self.agent_id
        ))
        
    def wait_for_response(self, source: Optional[str] = None, destination: Optional[str] = None,
                         channel: Optional[str] = None, timeout: int = 300) -> Optional[Message]:
        """Wait for a response matching specific criteria.
        
        Args:
            source: Optional source agent ID
            destination: Optional destination agent ID 
            channel: Optional channel name
            timeout: Maximum wait time in seconds
            
        Returns:
            Matching message or None if timeout expires
        """
        if source is None and channel is None:
            return None
            
        # Create set of observed message IDs to avoid returning already seen messages
        observed_message_ids = set()
        for message in self.filter_messages(source=source, destination=destination, channel=channel):
            observed_message_ids.add(message.message_id)
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            messages = self.filter_messages(source=source, destination=destination, channel=channel)
            # Look for unobserved messages
            for message in messages:
                if message.message_id not in observed_message_ids:
                    return message
                    
            # Sleep briefly to avoid busy wait
            time.sleep(0.1)
            
        return None
    
    def send_messages(self, messages: List[Message]):
        """Send multiple messages to the router.
        
        Args:
            messages: List of messages to send
        """
        for message in messages:
            self.send_message(message)

    def get_team_info(self) -> Optional[Dict]:
        """Get the team info for this agent if available.
        
        Returns:
            Dictionary representation of TeamInfo if available, None otherwise
        """
        return self._team_info 