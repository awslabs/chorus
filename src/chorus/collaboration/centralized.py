from chorus.collaboration.base import Collaboration
from chorus.data.dialog import Message
from chorus.helpers.communication import CommunicationHelper
from collections import deque
from pydantic import BaseModel

from chorus.data.context import TeamContext
from chorus.data.state import TeamState

LAST_REQUESTER_KEY = "last_requester"
TASK_QUEUE_KEY = "task_queue"
CURRENT_TASK_KEY = "current_task"


class TaskInfo(BaseModel):
    """Information about a queued task."""
    message: Message
    requester: str


@Collaboration.register('CentralizedCollaboration')
class CentralizedCollaboration(Collaboration):
    """Implements a centralized collaboration strategy between agents.

    This strategy coordinates multiple agents through a central coordinator that manages
    communication and task distribution. It maintains a queue of tasks when multiple
    requests come in, ensuring they are processed in order.
    """

    def process_message(self, team_context: TeamContext, team_state: TeamState, inbound_message: Message):
        data_store = team_state.get_collaboration_data_store()
        helper = CommunicationHelper(team_context)

        if inbound_message.event_type == "team_service":
            return

        # Initialize data store if needed
        if TASK_QUEUE_KEY not in data_store:
            data_store[TASK_QUEUE_KEY] = deque()
        if CURRENT_TASK_KEY not in data_store:
            data_store[CURRENT_TASK_KEY] = None

        requester = inbound_message.source
        
        if requester == self._coordinator:
            # Response from coordinator
            current_task = data_store[CURRENT_TASK_KEY]
            if current_task:
                # Send response to the original requester
                response_message = inbound_message.clone()
                response_message.source = team_context.agent_id
                response_message.destination = current_task.requester
                helper.send_raw_message(response_message)
                data_store[CURRENT_TASK_KEY] = None
                
                # Process next task in queue if any
                if data_store[TASK_QUEUE_KEY]:
                    next_task = data_store[TASK_QUEUE_KEY].popleft()
                    data_store[CURRENT_TASK_KEY] = next_task
                    next_message = next_task.message.clone()
                    next_message.source = team_context.agent_id
                    next_message.destination = self._coordinator
                    helper.send_raw_message(next_message)
        else:
            # New request from an agent
            task = TaskInfo(message=inbound_message, requester=requester)
            
            if data_store[CURRENT_TASK_KEY] is None:
                # No task being processed, handle immediately
                data_store[CURRENT_TASK_KEY] = task
                forward_message = inbound_message.clone()
                forward_message.source = team_context.agent_id
                forward_message.destination = self._coordinator
                helper.send_raw_message(forward_message)
            else:
                # Queue the task and notify requester
                data_store[TASK_QUEUE_KEY].append(task)
                queue_position = len(data_store[TASK_QUEUE_KEY])
                queue_message = Message(
                    source=team_context.agent_id,
                    destination=requester,
                    content=f"Your request has been queued. Current position in queue: {queue_position}"
                )
                helper.send_raw_message(queue_message)
        return

    def __init__(self, coordinator: str):
        """Initialize the centralized collaboration strategy.

        Args:
            coordinator (Agent): The coordinator agent that will manage collaboration.
        """
        super().__init__()
        self._coordinator = coordinator

    def get_coordinator(self):
        return self._coordinator

    def get_name(self):
        return "centralized"