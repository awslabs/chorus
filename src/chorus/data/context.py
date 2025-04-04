from typing import Dict
from typing import List
from typing import Optional
import uuid

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from chorus.communication.message_view_selectors import GlobalMessageViewSelector, MessageViewSelector
from chorus.data.agent_status import AgentStatus
from chorus.data.executable_tool import ExecutableTool
from chorus.data.resource import Resource
from chorus.data.team_info import TeamInfo
from chorus.util.status_manager import MultiAgentStatusManager
from chorus.communication.message_service import ChorusMessageClient


class AsyncExecutionRecord(BaseModel):
    """Record for tracking asynchronous action execution.

    Attributes:
        action_source: Source of the asynchronous action.
        action_channel: Channel used for the asynchronous action.
        tool_use_id: Unique identifier for the tool usage.
    """
    action_source: Optional[str] = None
    action_channel: Optional[str] = None
    tool_use_id: Optional[str] = None

class OrchestrationContext(BaseModel):
    """Base context for orchestration.

    This class provides the core context needed for orchestration, including tools,
    instructions, resources, artifacts and views.

    Attributes:
        tools: List of executable tools available.
        agent_instruction: Instructions for behavior.
        resources: List of available resources.
        artifacts: Dictionary mapping artifact names to their string values.
        views: List of accessible view identifiers.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tools: Optional[List[ExecutableTool]] = None
    agent_instruction: Optional[str] = None
    resources: Optional[List[Resource]] = None
    artifacts: Dict[str, str] = Field(default_factory=dict)
    views: Optional[List[str]] = None


class AgentContext(OrchestrationContext):
    """Context and utilities for an agent.

    This class extends OrchestrationContext to provide additional context and helper 
    methods needed by an agent to operate, including team information, messaging, 
    and status management.

    Attributes:
        agent_id: Unique identifier for the agent.
        team_info: Information about the agent's team.
        message_service: Service for handling agent communication.
        status_manager: Manager for tracking agent statuses.
        async_execution_cache: Dictionary mapping IDs to AsyncExecutionRecord objects
            for tracking asynchronous operations.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str
    team_info: Optional[TeamInfo] = None
    message_client: Optional[ChorusMessageClient] = None
    message_view_selector: MessageViewSelector = Field(default_factory=GlobalMessageViewSelector)
    status_manager: Optional[MultiAgentStatusManager] = None
    async_execution_cache: Dict[str, AsyncExecutionRecord] = Field(default_factory=dict)

    def get_tools(self) -> List[ExecutableTool]:
        """Get list of executable tools available to the agent.

        Returns:
            List of ExecutableTool objects, or empty list if none available.
        """
        return self.tools if self.tools is not None else []

    def get_resources(self) -> List[Resource]:
        """Get list of resources available to the agent.

        Returns:
            List of Resource objects, or empty list if none available.
        """
        return self.resources if self.resources is not None else []

    def get_agent_instruction(self) -> Optional[str]:
        """Get the instruction string for this agent.

        Returns:
            The agent instruction string if set, otherwise None.
        """
        return self.agent_instruction

    def get_current_datetime(self) -> Optional[str]:
        """Get current datetime string.

        Returns:
            Current datetime string if implemented, otherwise None.
        """
        return None

    def get_agent_id(self):
        """Get the agent's unique identifier.

        Returns:
            The agent's ID string.
        """
        return self.agent_id

    def get_views(self) -> Optional[List[str]]:
        """Get list of view identifiers accessible to the agent.

        Returns:
            List of view identifier strings if set, otherwise None.
        """
        return self.views
    
    def get_async_execution_cache(self) -> Dict[str, AsyncExecutionRecord]:
        """Get the cache of asynchronous execution records.

        Returns:
            Dictionary mapping IDs to AsyncExecutionRecord objects.
        """
        return self.async_execution_cache
    
    def set_message_client(self, message_client: ChorusMessageClient):
        """Install a message client for agent communication.

        Args:
            message_client: The ChorusMessageClient instance to install.
        """
        self.message_client = message_client
    
    def get_message_client(self) -> Optional[ChorusMessageClient]:
        """Get the message client for agent communication.

        Returns:
            The ChorusMessageClient instance.
        """
        return self.message_client

    def report_status(self, agent_id: str, status: AgentStatus):
        """Report an agent's status to the status manager.

        Args:
            agent_id: ID of the agent whose status is being reported.
            status: The AgentStatus to record.
        """
        if self.status_manager is not None:
            self.status_manager.record(agent_id, status)
    

class TeamContext(AgentContext):
    """Context for an agent team.

    Extends AgentContext to provide team-specific context and functionality.
    """