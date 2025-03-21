from chorus.data import Message
from chorus.agents import ConversationalTaskAgent
from chorus.data import EventType
from chorus.toolbox.examples import WeatherTool

instruction = """
You are an agent helping to suggest a good trip location close to the location the user provided for this weekend. Please suggest the location based on weather, safety, experience and budget.
"""

if __name__ == '__main__':
    weather_tool = WeatherTool()
    agent = ConversationalTaskAgent("Charlie", instruction=instruction, tools=[weather_tool], model_name="anthropic.claude-3-haiku-20240307-v1:0")
    context = agent.init_context()
    state = agent.init_state()
    context.message_service.send_messages([Message(source="human", destination="Charlie", content="Recommend a place to go for this weekend around New York")])
    agent.iterate(context, state)
    for turn in context.message_service.fetch_all_messages():
        print(turn.event_type, ">>>\n", turn.content, turn.actions, turn.observations)
