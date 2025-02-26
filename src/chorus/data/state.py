from typing import Any, Dict, Optional, Set
from pydantic import BaseModel, Field
from langchain_core.memory import BaseMemory

class AgentState(BaseModel):
    """Base class for agent state.

    A base class that represents the state of an agent.
    """
    pass


class PassiveAgentState(AgentState):
    """State for passive agents.

    A class that represents the state of a passive agent, which tracks processed messages.

    Attributes:
        processed_messages: Set of messages that have been processed by the agent
    """
    processed_messages: Set = Field(default_factory=set)


class TeamState(PassiveAgentState):
    """State for an agent team.

    A class that represents the state of a team of agents, extending PassiveAgentState
    with a service data store.

    Attributes:
        service_data_store: Dictionary storing data for different services
    """
    service_data_store: dict = Field(default_factory=dict)
    collaboration_data_store: dict = Field(default_factory=dict)

    def get_service_data_store(self, service_name: str) -> dict:
        """Gets the data store for a given service.

        Retrieves the data store dictionary for a specific service name,
        creating it if it doesn't exist.

        Args:
            service_name: Name of the service to get data store for

        Returns:
            Dictionary containing the service's data store
        """
        if service_name not in self.service_data_store:
            self.service_data_store[service_name] = {}
        return self.service_data_store[service_name]
    
    def get_collaboration_data_store(self) -> dict:
        """Gets the data store for a given collaboration.
        """
        return self.collaboration_data_store
    
class LangchainAgentState(PassiveAgentState):
    """State for LangChain agents.

    A class that represents the state of a LangChain agent, extending AgentState
    with a last message.

    Attributes:
        last_message: The last message processed by the agent
    """
    def __init__(self, memory:BaseMemory):
        self.conversation_context = memory

    def get_conversation_context(self, input) -> Dict[str, Any]:
        return self.conversation_context.load_memory_variables(input)
    
    def save_conversation_context(self, input, ouput) -> None:
        self.conversation_context.save_context(input, ouput)

