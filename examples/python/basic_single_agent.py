from chorus.agents import ConversationalTaskAgent
from chorus.toolbox import ArxivRetrieverTool
from chorus.core import Chorus

if __name__ == '__main__':
    paper_research_agent = ConversationalTaskAgent(
        tools=[ArxivRetrieverTool()],
        instruction="You are a paper research agent that can help find academic papers on Arxiv."
    ).name("PaperResearchAgent")

    chorus = Chorus(
        agents=[paper_research_agent]
    )

    chorus.start()
    
    answer_message = chorus.send_and_wait(
        destination="PaperResearchAgent",
        message="List papers on Arxiv about speculative decoding.",
        timeout=60  # Set a 60-second timeout instead of the default 300 seconds
    )


    # Print out the answer
    print("===========================================")
    print("Final Answer:")
    if answer_message is not None:
        print(answer_message.content)
    else:
        print("No response received within timeout. The agent may still be processing the request or encountered an error.")
    
        
    # Stop the chorus
    chorus.stop()
