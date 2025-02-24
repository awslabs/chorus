from chorus.data.context import AgentContext
from chorus.data.dialog import Message
from chorus.data.channel import Channel
from chorus.data.state import PassiveAgentState
from chorus.agents.passive_agent import PassiveAgent
from chorus.collaboration.centralized import CentralizedCollaboration
from chorus.teams.agent_team import Team
from chorus.core.runner import Chorus
from chorus.workspace.stop_conditions import NoActivityStopper

class SimpleAgent(PassiveAgent):
    def __init__(self, name: str):
        self.name = name
        super().__init__(name)
    
    def init_context(self) -> AgentContext:
        return AgentContext(agent_id=self.get_name())
    
    def respond(self, context: AgentContext, state: PassiveAgentState, inbound_message: Message) -> PassiveAgentState:
        return state
    
    def get_name(self) -> str:
        return self.name

def test_channel_message_sync(verbose=False):
    # Create three agents
    agent_a = SimpleAgent("agent_a")
    agent_b = SimpleAgent("agent_b")
    agent_c = SimpleAgent("agent_c")
    
    # Create a shared channel
    shared_channel = Channel(
        name="shared_channel",
        members={"agent_a", "agent_b", "agent_c"}
    )
    
    # Create a team with all agents
    team = Team(
        name="test_team",
        agents=[agent_a, agent_b, agent_c],
        collaboration=CentralizedCollaboration(coordinator=agent_a.get_name())
    )
    
    # Initialize Chorus with the team and channel
    chorus = Chorus(
        teams=[team],
        channels=[shared_channel],
        stop_conditions=[NoActivityStopper()]
    )
    
    # Send a message from agent_a to agent_b in the shared channel
    test_message = Message(
        source="agent_a",
        destination="agent_b",
        channel="shared_channel",
        content="Hello from agent_a!"
    )
    chorus.get_environment().send_message(test_message)
    
    # Run chorus for a short period to allow message synchronization
    chorus.run()
    
    # Verify that all agents can see the message
    for agent_id in ["agent_a", "agent_b", "agent_c"]:
        agent_context = chorus.get_agent_context(agent_id)
        messages = agent_context.message_service.fetch_all_messages()
        if verbose:
            print(f"Messages for {agent_id}: {messages}")
        assert len(messages) == 1, f"{agent_id} should have received the message"
        assert messages[0].content == "Hello from agent_a!"
        assert messages[0].source == "agent_a"
        assert messages[0].destination == "agent_b"
        assert messages[0].channel == "shared_channel"

# if __name__ == "__main__":
    # test_channel_message_sync(verbose=True)