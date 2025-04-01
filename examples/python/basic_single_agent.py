from chorus.agents import ConversationalTaskAgent
from chorus.toolbox import ArxivRetrieverTool
from chorus.core import Chorus

if __name__ == '__main__':
    paper_research_agent = ConversationalTaskAgent(
        name="PaperResearchAgent",
        tools=[ArxivRetrieverTool()],
        instruction="You are a paper research agent that can help find academic papers on Arxiv."
    )

    chorus = Chorus(
        agents=[paper_research_agent]
    )

    chorus.start()

    answer_message = chorus.send_and_wait(
        destination="PaperResearchAgent",
        message="List papers on Arxiv about speculative decoding."
    )

    # Print out the answer
    print("===========================================")
    print("Final Answer:")
    print(answer_message.content)

    chorus.stop()