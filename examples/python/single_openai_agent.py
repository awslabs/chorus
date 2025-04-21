from chorus.agents import ConversationalTaskAgent
from chorus.core import Chorus
from chorus.lms.openai_client import OpenAIClient
from chorus.toolbox import ArxivRetrieverTool
from chorus.prompters.interact.openai_tool_chat import OpenAIToolChatPrompter

if __name__ == '__main__':
    # Initialize the OpenAI client
    openai_client = OpenAIClient(
        model_name="gpt-4o-mini",
        # You can provide api_key here or set OPENAI_API_KEY environment variable
        # api_key="your-openai-api-key"
    )
    
    # Initialize the OpenAI-specific prompter
    openai_prompter = OpenAIToolChatPrompter()
    
    # Create a conversational agent with OpenAI and ArxivRetrieverTool
    arxiv_agent = ConversationalTaskAgent(
        tools=[ArxivRetrieverTool()],
        instruction="You are a research assistant that can search for academic papers on Arxiv.",
        lm=openai_client,
        prompter=openai_prompter
    ).name("OpenAIArxivAssistant")

    # Initialize Chorus with the OpenAI agent
    chorus = Chorus(
        agents=[arxiv_agent]
    )

    # Start Chorus
    chorus.start()
    
    # Send a message to the agent and wait for a response
    answer_message = chorus.send_and_wait(
        destination="OpenAIArxivAssistant",
        message="Find papers on Arxiv about large language models and transformers.",
        timeout=180
    )

    # Print the response
    print("===========================================")
    print("Response from OpenAI Arxiv Assistant:")
    if answer_message is not None:
        print(answer_message.content)
    else:
        print("No response received within timeout.")
    
    # Stop Chorus
    chorus.stop() 