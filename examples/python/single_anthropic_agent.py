from chorus.agents import ConversationalTaskAgent
from chorus.toolbox import ArxivRetrieverTool
from chorus.core import Chorus
from chorus.lms.anthropic_client import AnthropicClient
from chorus.prompters.interact.anthropic_tool_chat import AnthropicToolChatPrompter

if __name__ == '__main__':
    # Initialize the Anthropic client
    anthropic_client = AnthropicClient(
        model_name="claude-3-7-sonnet-20250219",
        # You can provide api_key here or set ANTHROPIC_API_KEY environment variable
        # api_key="your-anthropic-api-key"
    )
    
    # Initialize the Anthropic-specific prompter
    anthropic_prompter = AnthropicToolChatPrompter()
    
    # Create a conversational agent with Anthropic and ArxivRetrieverTool
    arxiv_agent = ConversationalTaskAgent(
        tools=[ArxivRetrieverTool()],
        instruction="You are a research assistant that can search for academic papers on Arxiv.",
        lm=anthropic_client,
        prompter=anthropic_prompter
    ).name("AnthropicArxivAssistant")

    # Initialize Chorus with the Anthropic agent
    chorus = Chorus(
        agents=[arxiv_agent]
    )

    # Start Chorus
    chorus.start()
    
    # Send a message to the agent and wait for a response
    answer_message = chorus.send_and_wait(
        destination="AnthropicArxivAssistant",
        message="Find papers on Arxiv about diffusion models for image generation.",
        timeout=180
    )

    # Print the response
    print("===========================================")
    print("Response from Anthropic Arxiv Assistant:")
    if answer_message is not None:
        print(answer_message.content)
    else:
        print("No response received within timeout.")
    
    # Stop Chorus
    chorus.stop() 