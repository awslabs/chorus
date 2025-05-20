import time
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
    
    def init_context(self) -> AgentContext:
        return AgentContext(agent_id=self.get_name())
    
    def respond(self, context: AgentContext, state: PassiveAgentState, inbound_message: Message) -> PassiveAgentState:
        return state

def test_channel_message_sync(verbose=False):
    # Create three agents
    agent_a = SimpleAgent().name("agent_a")
    agent_b = SimpleAgent().name("agent_b")
    agent_c = SimpleAgent().name("agent_c")
    
    # Create a shared channel
    shared_channel = Channel(
        name="shared_channel",
        members=[agent_a.identifier(), agent_b.identifier(), agent_c.identifier()]
    )
    
    # Create a team with all agents
    team = Team(
        name="test_team",
        agents=[agent_a, agent_b, agent_c],
        collaboration=CentralizedCollaboration(coordinator=agent_a.identifier())
    )
    
    # Initialize Chorus with the team and channel
    chorus = Chorus(
        teams=[team],
        channels=[shared_channel],
        stop_conditions=[NoActivityStopper()]
    )
    try:
        chorus.start()
        time.sleep(5)
        # Send a message from agent_a to agent_b in the shared channel
        test_message = Message(
            source=agent_a.identifier(),
            destination=agent_b.identifier(),
            channel=shared_channel.name,
            content="Hello from agent_a!"
        )
        chorus.send_message(test_message)
        
        # Verify that the message is in the global context
        global_messages = chorus.get_global_context().fetch_all_messages()
        
        # Check if message is present in the global context
        assert len(global_messages) >= 1, "Global context should have at least one message"
        
        # Find our test message
        found_message = None
        for msg in global_messages:
            if (msg.source == agent_a.identifier() and 
                msg.destination == agent_b.identifier() and 
                msg.channel == shared_channel.name and
                msg.content == "Hello from agent_a!"):
                found_message = msg
                break
        
        assert found_message is not None, "Test message should be in the global context"
    finally:
        chorus.stop()