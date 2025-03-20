import pytest
import threading
import time
from chorus.data import Message
from chorus.agents import CollaborativeAgent
from chorus.toolbox import ArxivRetrieverTool
from chorus.core.runner import Chorus
from chorus.workspace.stop_conditions import NoActivityStopper

def test_async_message_delivery():
    # Create agents
    charlie = CollaborativeAgent(
        name="Charlie",
        reachable_agents={
            "Thomas": "This is another agent with name Thomas.",
            "human": "This is the human user."
        },
        allow_waiting=True
    )
    thomas = CollaborativeAgent(
        name="Thomas",
        reachable_agents={"Charlie": "This is another agent with name Charlie."},
        tools=[ArxivRetrieverTool()],
        allow_waiting=True
    )

    # Initialize Chorus with 30 second timeout
    simulator = Chorus(agents=[charlie, thomas], stop_conditions=[NoActivityStopper(30)])
    
    # Send message from Charlie to Thomas
    test_message = "Hello Thomas, this is a test message."
    simulator.get_environment().send_message(
        source="Charlie",
        destination="Thomas",
        message=Message(content=test_message)
    )
    
    # Create and start simulator thread
    simulator_thread = threading.Thread(target=simulator.run)
    simulator_thread.daemon = True  # Set as daemon so it exits when main thread exits
    simulator_thread.start()
    
    # Wait and check for message delivery with timeout
    max_wait_time = 30  # seconds
    start_time = time.time()
    message_received = False
    
    while time.time() - start_time < max_wait_time and not message_received:
        # Check if Thomas received the message
        thomas_context = simulator.get_agent_context("Thomas")
        messages = thomas_context.message_service.fetch_all_messages()
        
        message_received = any(
            msg.source == "Charlie" and msg.destination == "Thomas" and msg.content == test_message 
            for msg in messages
        )
        
        if not message_received:
            time.sleep(0.5)  # Wait before checking again
    
    # Stop the simulator thread if it's still running
    simulator.stop()
    simulator_thread.join(timeout=1)
    
    # Assert message was received
    assert message_received, f"Thomas did not receive the message from Charlie within {max_wait_time} seconds"

if __name__ == '__main__':
    pytest.main([__file__])