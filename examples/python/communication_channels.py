from chorus.core import Chorus
from chorus.agents import CollaborativeAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.data.channel import Channel
from chorus.toolbox import DuckDuckGoWebSearchTool, WebRetrieverTool, SerperWebSearchTool
from chorus.workspace import NoActivityStopper
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--use_serper_search', action='store_true', help='Use SerperWebSearch instead of DuckDuckGo')
    args = parser.parse_args()

    # Select the search tool based on the flag
    search_tool = SerperWebSearchTool() if args.use_serper_search else DuckDuckGoWebSearchTool()

    # Define communication channel
    news_channel = Channel(
        name="news_channel",
        members=["NewsAnchor", "NewsReporter", "WeatherReporter"]
    )

    # Create agents
    news_anchor = CollaborativeAgent(
        instruction="""You are a news anchor who coordinates news broadcasts.
        - Monitor the news_channel for all updates
        - When receiving news from reporters, format it for broadcast
        - Send all formatted broadcasts to human
        - Maintain a professional broadcasting tone
        - Prioritize urgent news when received""",
    ).name("NewsAnchor")

    news_reporter = CollaborativeAgent(
        instruction="""You are a news reporter who gathers and reports news.
        - Use web search to find current news
        - Report all news (both regular and urgent) on "news_channel" channel
        - Focus on factual reporting
        - Mark urgent news with [URGENT] prefix""",
        tools=[
            search_tool,
            WebRetrieverTool()
        ]
    ).name("NewsReporter")

    weather_reporter = CollaborativeAgent(
        instruction="""You are a weather reporter who reports weather updates.
        - Use web search to find weather information
        - Report weather updates on "news_channel" channel
        - Keep updates concise and informative""",
        tools=[
            search_tool,
            WebRetrieverTool()
        ]
    ).name("WeatherReporter")

    # Create team
    news_team = Team(
        name="NewsTeam",
        agents=[news_anchor, news_reporter, weather_reporter],
        collaboration=CentralizedCollaboration(
            coordinator=news_anchor.get_name()
        )
    )

    # Initialize Chorus with channel
    chorus = Chorus(
        teams=[news_team],
        channels=[news_channel],
        stop_conditions=[NoActivityStopper()]
    )
    chorus.start()
    
    # Start with an initial message
    chorus.send_and_wait(
        source="human",
        destination="NewsReporter",
        message="Please find and report some current technology news."
    )

    chorus.stop()

if __name__ == "__main__":
    main()