from chorus.agents import ConversationalTaskAgent
from chorus.collaboration import CentralizedCollaboration
from chorus.teams import Team
from chorus.teams.services import TeamToolbox
from chorus.teams.toolbox import AsyncTeamToolClient
from chorus.toolbox import ArxivRetrieverTool
from chorus.core import Chorus
from chorus.workspace import NoActivityStopper

def main():
    arxiv_retriever_tool = ArxivRetrieverTool()
    paper_research_agent = ConversationalTaskAgent(
        tools=[AsyncTeamToolClient(arxiv_retriever_tool)],
        instruction="You are a paper research agent that can help find academic papers on Arxiv."
    ).name("PaperResearchAgent")

    team = Team(
        name="PaperResearchTeam",
        agents=[paper_research_agent],
        collaboration=CentralizedCollaboration(coordinator=paper_research_agent.get_name()),
        services=[TeamToolbox(
            tools=[arxiv_retriever_tool]
        )]
    )
    chorus = Chorus(
        teams=[team],
        stop_conditions=[NoActivityStopper()],
    )
    chorus.start()

    chorus.send_and_wait(
        source="human",
        destination="PaperResearchAgent",
        message="List papers on Arxiv about speculative decoding."
    )
    chorus.stop()
    
    # Print out the answer
    answer_message = chorus.get_environment().filter_messages(
        source="PaperResearchAgent",
        destination="human"
    )[-1]
    print("===========================================")
    print("Final Answer:")
    print(answer_message.content)

if __name__ == "__main__":
    main()