from chorus.agents import ToolChatAgent
from chorus.toolbox import ArxivRetrieverTool
from chorus.core import Chorus
from chorus.workspace import NoActivityStopper

if __name__ == '__main__':
    paper_research_agent = ToolChatAgent(
        name="PaperResearchAgent",
        tools=[ArxivRetrieverTool()],
        instruction="You are a paper research agent that can help find academic papers on Arxiv."
    )

    chorus = Chorus(
        agents=[paper_research_agent],
        stop_conditions=[NoActivityStopper()]
    )

    chorus.get_environment().send_message(
        source="human",
        destination="PaperResearchAgent",
        content="List papers on Arxiv about speculative decoding."
    )
    chorus.run()
    # Print out the answer
    answer_message = chorus.get_environment().filter_messages(
        source="PaperResearchAgent",
        destination="human"
    )[-1]
    print("===========================================")
    print("Final Answer:")
    print(answer_message.content)
