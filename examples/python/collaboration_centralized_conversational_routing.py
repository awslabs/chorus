from chorus.agents import  TaskCoordinatorAgent, ConversationalTaskAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.core.runner import Chorus

from chorus.toolbox import ArxivRetrieverTool
from chorus.toolbox import WebRetrieverTool
from chorus.toolbox import DuckDuckGoWebSearchTool
from chorus.workspace.stop_conditions import NoActivityStopper


def main():
    routing_agent = TaskCoordinatorAgent(
        instruction="""
        Do not do any task by yourself, if you don't have a agent to answer the question, tell the user that don't have a agent to answer the question.
        """,
        reachable_agents={
            "NewsSearchAgent": "An agent that can help user to find news related to artificial intelligence and summarize them by search web and access pages.",
            "ResearchPaperSearchAgent": "An agent that can help user to find research papers and summarize them by search arxiv and access pages.",
            "MachineLearningQAAgent": "An agent that can help user to explain the concept of machine learning and artificial intelligence."
        }
    ).name("MachineLearningQARoutingAgent")
    news_search_agent = ConversationalTaskAgent(
        instruction="You can help user to find news and summarize them by search web and access pages.",
        tools=[
            DuckDuckGoWebSearchTool(),
            WebRetrieverTool()
        ]
    ).name("NewsSearchAgent")
    research_paper_search_agent = ConversationalTaskAgent(
        instruction="You can help user to find research papers and summarize them by search arxiv and access pages.",
        tools=[ArxivRetrieverTool()]
    ).name("ResearchPaperSearchAgent")
    machine_learning_qa_agent = ConversationalTaskAgent(
        instruction="You can help user to explain the concept of machine learning and artificial intelligence."
    ).name("MachineLearningQAAgent")

    team = Team(
        name="MachineLearningQATeam",
        agents=[routing_agent, news_search_agent, research_paper_search_agent, machine_learning_qa_agent],
        collaboration=CentralizedCollaboration(
            coordinator=routing_agent.get_name()
        )
    )

    chorus = Chorus(
        teams=[team],
        stop_conditions=[NoActivityStopper()]
    )

    chorus.start()
    
    chorus.send_and_wait(
        source="human",
        destination=team.identifier(),
        message="Explain what is logistic regression."
    )

    chorus.stop()

if __name__ == "__main__":
    main()