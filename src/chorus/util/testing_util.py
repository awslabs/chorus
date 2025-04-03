from chorus.communication.message_service import ChorusMessageClient
import uuid
from typing import Dict, List, Optional, Set
from chorus.data.dialog import Message


class MockMessageClient(ChorusMessageClient):
    def __init__(self, agent_id: str):
        """Initialize a mock message client without actual ZMQ connections.
        
        Args:
            agent_id: ID of the agent this client belongs to
            router_host: Placeholder for compatibility
            router_port: Placeholder for compatibility
        """
        self.agent_id = agent_id
        self._message_history = []
        self._local_message_ids = set()
        self._team_info = None
        self._running = True
    
    def _register(self):
        """Mock registration - no actual ZMQ connection."""
        pass
    
    def start(self):
        """Start the mock client - no threading needed."""
        self._running = True
    
    def stop(self):
        """Stop the mock client."""
        self._running = False
    
    def send_message(self, message: Message):
        """Store a message in the local history.
        
        Args:
            message: Message to store
        """
        if message.message_id is None:
            message.message_id = str(uuid.uuid4().hex)
            
        # Add to local message history
        if message.message_id not in self._local_message_ids:
            self._message_history.append(message)
            self._local_message_ids.add(message.message_id)
    
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
        """Mock state update - no actual sending occurs."""
        pass
    
    def send_stop_ack(self):
        """Mock stop acknowledgment - no actual sending occurs."""
        self._running = False
    
    def wait_for_response(self, source: Optional[str] = None, destination: Optional[str] = None,
                         channel: Optional[str] = None, timeout: int = 300) -> Optional[Message]:
        """Return the first matching message in history without actually waiting.
        
        Args:
            source: Optional source agent ID
            destination: Optional destination agent ID 
            channel: Optional channel name
            timeout: Ignored in mock implementation
            
        Returns:
            First matching message or None if none found
        """
        messages = self.filter_messages(source=source, destination=destination, channel=channel)
        return messages[0] if messages else None
    
    def send_messages(self, messages: List[Message]):
        """Store multiple messages in the local history.
        
        Args:
            messages: List of messages to store
        """
        for message in messages:
            self.send_message(message)
    
    def get_team_info(self) -> Optional[Dict]:
        """Get the mock team info.
        
        Returns:
            Mock team info if set, None otherwise
        """
        return self._team_info
    
    def set_team_info(self, team_info: Dict):
        """Set mock team info for testing.
        
        Args:
            team_info: Team info dictionary to store
        """
        self._team_info = team_info