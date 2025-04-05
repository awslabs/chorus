import json
import uuid
from enum import Enum
from typing import Any, Dict, Optional

# Message types for ZMQ communication
class MessageType(str, Enum):
    # Agent registration and management
    REGISTER = "register"
    REGISTER_ACK = "register_ack"
    
    # State management
    GET_STATE = "get_state"
    STATE_UPDATE = "state_update"
    DUMP_STATE = "dump_state"
    
    # Agent messaging
    AGENT_MESSAGE = "agent_message"
    ROUTER_MESSAGE = "router_message"
    
    # Team management
    TEAM_INFO = "team_info"
    
    # Status tracking
    STATUS_UPDATE = "status_update"
    
    # Control signals
    STOP = "stop"
    STOP_ACK = "stop_ack"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"

class ZMQMessage:
    """Protocol message for ZMQ-based agent communication"""
    
    def __init__(
        self, 
        msg_type: MessageType, 
        agent_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        msg_id: Optional[str] = None
    ):
        self.msg_type = msg_type
        self.agent_id = agent_id
        self.payload = payload or {}
        self.msg_id = msg_id or str(uuid.uuid4())
        
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps({
            "msg_type": self.msg_type.value,
            "agent_id": self.agent_id,
            "payload": self.payload,
            "msg_id": self.msg_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "ZMQMessage":
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls(
            msg_type=MessageType(data["msg_type"]),
            agent_id=data["agent_id"],
            payload=data["payload"],
            msg_id=data["msg_id"]
        ) 