from chorus.core import Chorus
from chorus.agents import AsyncToolChatAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.data.channel import Channel
from chorus.data.trigger import MessageTrigger
from chorus.data.dialog import Role
from chorus.data.context import ChorustionContext
from chorus.toolbox import DuckDuckGoWebSearchTool, WebRetrieverTool, SerperWebSearchTool
from chorus.workspace import NoActivityStopper
import argparse

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--use_serper_search', action='store_true', help='Use SerperWebSearch instead of DuckDuckGo')
    args = parser.parse_args()

    # Select the search tool based on the flag
    search_tool = SerperWebSearchTool() if args.use_serper_search else DuckDuckGoWebSearchTool()

    # Define communication channels
    news_channel = Channel(
        name="news_channel",
        members=["NewsMonitor", "NewsAnalyst"]
    )

    # Define different contexts for the analyst
    regular_context = ChorustionContext(
        agent_instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="news_channel" description="Channel for news monitoring and analysis"/>
        </channels>
        
        You are in regular monitoring mode:
        - Analyze news with standard depth
        - Focus on factual reporting
        - Maintain neutral tone""",
        tools=[search_tool, WebRetrieverTool()]
    )

    urgent_context = ChorustionContext(
        agent_instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="news_channel" description="Channel for news monitoring and analysis"/>
        </channels>
        
        You are in urgent monitoring mode:
        - Provide immediate analysis of breaking news
        - Focus on key impacts and implications
        - Highlight critical points
        - Use [URGENT] prefix in responses""",
        tools=[search_tool, WebRetrieverTool()]
    )

    # Create agents
    monitor = AsyncToolChatAgent(
        "NewsMonitor",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="news_channel" description="Channel for news monitoring and analysis"/>
        </channels>
        
        You are a news monitoring agent:
        - Use web search to find current news
        - Tag urgent news with [URGENT] prefix
        - Send all news to the news_channel
        - For urgent news, send to NewsAnalyst directly""",
        tools=[search_tool, WebRetrieverTool()]
    )

    analyst = AsyncToolChatAgent(
        "NewsAnalyst",
        instruction="""You are a news analysis agent:
        - Analyze news shared in the news_channel
        - Provide detailed analysis of news impact
        - Switch between regular and urgent analysis modes based on triggers""",
        tools=[search_tool, WebRetrieverTool()]
    )

    # Create triggers for context switching
    urgent_trigger = MessageTrigger(
        source="NewsMonitor",
    )

    regular_trigger = MessageTrigger(
        channel="news_channel",
    )

    # Set up context switching for the analyst
    analyst.on(urgent_trigger, urgent_context)
    analyst.on(regular_trigger, regular_context)

    # Create team
    news_team = Team(
        name="NewsTeam",
        agents=[monitor, analyst],
        collaboration=CentralizedCollaboration(
            coordinator=monitor.get_name()
        )
    )

    # Initialize Chorus
    chorus = Chorus(
        teams=[news_team],
        channels=[news_channel],
        stop_conditions=[NoActivityStopper()],
        visual=True,
        visual_port=5001
    )

    # Start with an initial message
    chorus.get_environment().send_message(
        source="human",
        destination="NewsMonitor",
        content="Please monitor and analyze current technology news, with special attention to any urgent developments."
    )

    # Run the simulation
    chorus.run()
