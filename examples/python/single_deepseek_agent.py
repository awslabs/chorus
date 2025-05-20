from chorus.agents import ConversationalTaskAgent
from chorus.toolbox import ArxivRetrieverTool
from chorus.core import Chorus
from chorus.lms.deepseek_client import DeepseekClient
from chorus.prompters.interact.openai_tool_chat import OpenAIToolChatPrompter

if __name__ == '__main__':
    # Initialize the Deepseek client
    deepseek_client = DeepseekClient(
        model_name="deepseek-chat",
        # You can provide api_key here or set DEEPSEEK_API_KEY environment variable
        # api_key="your-deepseek-api-key"
    )
    
    # Initialize the OpenAI-specific prompter (Deepseek uses OpenAI-compatible format)
    openai_prompter = OpenAIToolChatPrompter()
    
    # Create a conversational agent with Deepseek and ArxivRetrieverTool
    arxiv_agent = ConversationalTaskAgent(
        tools=[ArxivRetrieverTool()],
        instruction="You are a research assistant that can search for academic papers on Arxiv.",
        lm=deepseek_client,
        prompter=openai_prompter
    ).name("DeepseekArxivAssistant")

    # Initialize Chorus with the Deepseek agent
    chorus = Chorus(
        agents=[arxiv_agent]
    )

    # Start Chorus
    chorus.start()
    
    # Send a message to the agent and wait for a response
    answer_message = chorus.send_and_wait(
        destination="DeepseekArxivAssistant",
        message="Find recent papers on Arxiv about quantum computing algorithms.",
        timeout=60  # Set a 60-second timeout
    )

    # Print the response
    print("===========================================")
    print("Response from Deepseek Arxiv Assistant:")
    if answer_message is not None:
        print(answer_message.content)
    else:
        print("No response received within timeout.")
    
    # Stop Chorus
    chorus.stop() 