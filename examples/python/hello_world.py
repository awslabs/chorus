from chorus.core import Chorus

from chorus.agents import  SynchronizedCoordinatorAgent, ToolChatAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration

from chorus.toolbox import WebRetrieverTool
from chorus.toolbox import DuckDuckGoWebSearchTool

from chorus.workspace import NoActivityStopper


if __name__ == '__main__':
    coordinator_agent = SynchronizedCoordinatorAgent(
        "FitnessAnsweringAgent",
        instruction="""
        Do not do any task by yourself, always try to call other agents.
        If there is no relevant agent available, tell the user that you do not have a agent to answer the question.
        Make your answer comprehensive and detailed.
        """,
        reachable_agents={
            "FactResearchAgent": "An agent that can help user to find facts related to fitness and summarize them by search web and access pages.",
            "KnowledgeAgent": "An agent that can help user to answer general questions about fitness." 
        }
    )
    fact_research_agent = ToolChatAgent(
        "FactResearchAgent",
        instruction="You can help user to find facts related to fitness and summarize them by search web and access pages.",
        tools=[
            DuckDuckGoWebSearchTool(),
            WebRetrieverTool()
        ]
    )
    knowledge_agent = ToolChatAgent(
        "KnowledgeAgent",
        instruction="Help user to answer general questions about fitness, nutrition, exercise and healthy lifestyle.",
    )

    team = Team(
        name="HelloWorldTeam",
        agents=[coordinator_agent, fact_research_agent, knowledge_agent],
        collaboration=CentralizedCollaboration(
            coordinator=coordinator_agent.get_name()
        )
    )

    chorus = Chorus(
        teams=[team],
        stop_conditions=[NoActivityStopper()]
    )

    chorus.get_environment().send_message(
        source="human",
        destination=team.get_identifier(),
        content="What are the best parks in New York City for running?"
    )
    chorus.run()