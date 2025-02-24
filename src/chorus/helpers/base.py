from chorus.data.context import AgentContext


class AgentHelper(object):
    """
    Base class for helping develop custom orchestration logic for agents.
    """

    def __init__(self, context: AgentContext):
        self._context = context

    def get_context(self):
        return self._context
    
    def get_agent_id(self):
        return self._context.agent_id
