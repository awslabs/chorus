from typing import Set

from pydantic import Field
from chorus.core.runner import Chorus
from chorus.agents import Agent
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.dialog import Message
from chorus.data.channel import Channel
from chorus.helpers.communication import CommunicationHelper
import time
import random

class SlowAgentState(AgentState):
    iterations: int = 0
    processed_message_ids: Set[str] = Field(default_factory=set)

class SlowAgent(Agent):
    """A demo agent that processes messages slowly to demonstrate visual debugging."""
    
    def __init__(self, name: str, delay_range: tuple = (1, 3), crash_after: int = None):
        self.name = name
        self.delay_range = delay_range
        self.crash_after = crash_after
        
    def init_context(self) -> AgentContext:
        return AgentContext(agent_id=self.name)
    
    def init_state(self) -> SlowAgentState:
        state = SlowAgentState()
        state.iterations = 0
        return state
    
    def iterate(self, context: AgentContext, state: SlowAgentState) -> AgentState:
        comm = CommunicationHelper(context)
        state.iterations += 1
        
        # Simulate some processing with random delays and output
        delay = random.uniform(*self.delay_range)
        print(f"{context.agent_id}: Starting processing (iteration {state.iterations})...")
        time.sleep(delay)
        print(f"{context.agent_id}: Processing step 1...")
        time.sleep(delay)
        print(f"{context.agent_id}: Processing step 2...")
        time.sleep(delay)
        
        # Process any messages
        for message in context.message_service.fetch_all_messages():
            print(f"{context.agent_id}: Received message: {message.content}")
            if message.message_id not in state.processed_message_ids:
                state.processed_message_ids.add(message.message_id)
                # Send a response
                comm.send(source=context.agent_id, destination=message.source, content="Processed your message")
        # Simulate a crash after certain iterations if specified
        if self.crash_after and state.iterations >= self.crash_after:
            print(f"{context.agent_id}: About to crash!")
            raise Exception(f"Simulated crash in {context.agent_id} after {state.iterations} iterations")
            
        print(f"{context.agent_id}: Finished processing")
        return state

def main():
    # Create some agents with different processing delays
    # Make MediumAgent crash after 3 iterations
    agents = [
        SlowAgent("FastAgent", (3, 5), crash_after=2),
        SlowAgent("MediumAgent", (5, 10), crash_after=3),  # This agent will crash
        SlowAgent("SlowAgent", (10, 30))
    ]
    
    # Create a shared channel for all agents
    channel = Channel(
        name="shared_channel",
        members={"FastAgent", "MediumAgent", "SlowAgent"}
    )
    
    # Create the Chorus runner with visual debugging enabled
    runner = Chorus(
        agents=agents,
        channels=[channel],
        visual=True,  # Enable visual debugging
        visual_port=5000  # Use port 5000 for the web interface
    )
    
    # Send some test messages
    env = runner.get_environment()
    test_messages = [
        Message(source="FastAgent", destination="MediumAgent", content="Hello from FastAgent!"),
        Message(source="MediumAgent", destination="SlowAgent", content="Hello from MediumAgent!"),
        Message(source="SlowAgent", destination="FastAgent", content="Hello from SlowAgent!")
    ]
    
    for msg in test_messages:
        env.send_message(msg)
    
    # Run the chorus
    print("Starting Chorus with visual debugging...")
    print("Open your browser to http://localhost:5000 to see the agent outputs")
    print("MediumAgent will crash after 3 iterations")
    print("When the crash occurs, you can check the error in the visual debugger")
    print("Press Enter to exit after checking the error")
    
    try:
        runner.run()
    except (KeyboardInterrupt, SystemError) as e:
        if isinstance(e, SystemError):
            print("\nAn agent has crashed. Check the visual debugger for details.")
        else:
            print("\nStopping Chorus...")

if __name__ == "__main__":
    main()