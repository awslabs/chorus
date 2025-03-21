from typing import List
from chorus.data.dialog import Message
from chorus.data.context import AgentContext
from chorus.data.message_view import MessageView
from chorus.data.state import AgentState

def select_message_view(context: AgentContext, state: AgentState, message_history: List[Message]) -> MessageView:
    """Select a message view for the agent.
    """
    all_messages = message_history + state.internal_events
    all_messages.sort(key=lambda x: x.timestamp)
    return context.message_view_selector.select(all_messages, message_history[-1])