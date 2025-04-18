from chorus.core import Chorus

from chorus.agents import  TaskCoordinatorAgent, ConversationalTaskAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration

from chorus.toolbox import WebRetrieverTool
from chorus.toolbox import DuckDuckGoWebSearchTool

from chorus.helpers.communication import CommunicationHelper


def run_chorus(chorus):
    chorus.run()


def main():
    coordinator_agent = TaskCoordinatorAgent(
        instruction="""
        Do not do any task by yourself, always try to call other agents.
        If there is no relevant agent available, tell the user that you do not have a agent to answer the question.
        Make your answer comprehensive and detailed.
        """,
        reachable_agents={
            "FactResearchAgent": "An agent that can help user to find facts related to fitness and summarize them by search web and access pages.",
            "KnowledgeAgent": "An agent that can help user to answer general questions about fitness, healthy lifestyle, nutrition, exercise, etc." 
        }
    ).name("FitnessAnsweringAgent")
    fact_research_agent = ConversationalTaskAgent(
        instruction="You can help user to find facts related to fitness and summarize them by search web and access pages.",
        tools=[
            DuckDuckGoWebSearchTool(),
            WebRetrieverTool()
        ]
    ).name("FactResearchAgent")
    knowledge_agent = ConversationalTaskAgent(
        instruction="Help user to answer general questions about fitness, nutrition, exercise and healthy lifestyle.",
    ).name("KnowledgeAgent")

    team = Team(
        name="HelloWorldTeam",
        agents=[coordinator_agent, fact_research_agent, knowledge_agent],
        collaboration=CentralizedCollaboration(
            coordinator=coordinator_agent.get_name()
        )
    )

    chorus = Chorus(
        teams=[team]
    )


    # Start Chorus in a thread
    chorus.start()

    comm = CommunicationHelper(chorus.get_global_context())
    comm.send(
        destination="FitnessAnsweringAgent",
        content="What is the calorie of an apple in general?"
    )

    response = comm.wait(
        source="FitnessAnsweringAgent",
    )
    print("Response received:")
    print(response.content)

    chorus.stop()

if __name__ == "__main__":
    main()