from chorus.data import Message
from chorus.agents import ConversationalTaskAgent
from chorus.data import EventType
from chorus.toolbox.examples import WeatherTool
from unittest.mock import MagicMock

instruction = """
You are an agent helping to suggest a good trip location close to the location the user provided for this weekend. Please suggest the location based on weather, safety, experience and budget.
"""

if __name__ == '__main__':
    weather_tool = WeatherTool()
    agent = ConversationalTaskAgent(instruction=instruction, tools=[weather_tool], model_name="anthropic.claude-3-haiku-20240307-v1:0").name("Charlie")
    context = agent.init_context()
    state = agent.init_state()
    
    # Create a message to test
    message = Message(source="human", destination="Charlie", content="Recommend a place to go for this weekend around New York")
    
    # Set up a message client mock
    message_client_mock = MagicMock()
    message_client_mock.fetch_all_messages.return_value = [message]
    context.get_message_client = MagicMock(return_value=message_client_mock)
    
    # Run iteration
    agent.iterate(context, state)
    
    # Print messages
    for turn in context.get_message_client().fetch_all_messages():
        print(turn.event_type, ">>>\n", turn.content, turn.actions, turn.observations)
