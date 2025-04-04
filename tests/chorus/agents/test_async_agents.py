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
        reachable_agents={
            "Thomas": "This is another agent with name Thomas.",
            "human": "This is the human user."
        },
        allow_waiting=True
    ).name("Charlie")
    
    thomas = CollaborativeAgent(
        reachable_agents={"Charlie": "This is another agent with name Charlie."},
        tools=[ArxivRetrieverTool()],
        allow_waiting=True
    ).name("Thomas")

    # Initialize Chorus with 30 second timeout
    chorus = Chorus(agents=[charlie, thomas], stop_conditions=[NoActivityStopper(30)])
    chorus.start()
    time.sleep(5)
    
    # Send message from Charlie to Thomas
    test_message = "Hello Thomas, this is a test message."
    chorus.send_message(
        source="Charlie",
        destination="Thomas",
        message=test_message
    )
    
    # Wait and check for message delivery with timeout
    max_wait_time = 30  # seconds
    start_time = time.time()
    message_received = False
    
    while time.time() - start_time < max_wait_time and not message_received:
        # Check if message was received by getting all messages from the global context
        messages = chorus.get_global_context().fetch_all_messages()
        
        message_received = any(
            msg.source == "Charlie" and msg.destination == "Thomas" and msg.content == test_message 
            for msg in messages
        )
        
        if not message_received:
            time.sleep(0.5)  # Wait before checking again
    
    # Stop the simulator thread if it's still running
    chorus.stop()
    
    # Assert message was received
    assert message_received, f"Thomas did not receive the message from Charlie within {max_wait_time} seconds"

if __name__ == '__main__':
    pytest.main([__file__])