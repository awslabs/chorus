import logging
from typing import Optional, List

# Ensure required packages are installed
try:
    from langchain.agents import AgentType, initialize_agent
    from langchain.memory import ConversationBufferMemory
    from langchain.tools import Tool
    from langchain_aws import ChatBedrock
except ImportError:
    raise ImportError("This example requires boto3, langchain, and langchain_aws. "
                     "Please install them with `pip install boto3 langchain langchain-core langchain-aws`")


from chorus.core import Chorus
from chorus.agents import LangChainAgentAdapter
from chorus.workspace import NoActivityStopper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define tools that will be used by LangChain
def get_weather(location):
    """Get the weather for a location."""
    return f"The weather in {location} is sunny and 75 degrees."

def get_time(timezone):
    """Get the current time in a timezone."""
    return f"The current time in {timezone} is 10:00 AM."


class ExampleLangChainAgent(LangChainAgentAdapter):
    @staticmethod
    def create_agent():
        """Create an agent with tools and LLM in a separate function to avoid pickling issues."""
        # Create tools for LangChain
        tools = [
            Tool(
                name="Weather",
                func=get_weather,
                description="Useful for getting the weather in a specific location",
            ),
            Tool(
                name="Time",
                func=get_time,
                description="Useful for getting the current time in a specific timezone",
            ),
        ]
        
        # Create a Claude model using BedrockChat
        bedrock_llm = ChatBedrock(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region_name="us-west-2",  # Change to your region
            # credentials_profile_name="default",  # Uncomment and set if needed
            model_kwargs={
                "temperature": 0.0,
                "max_tokens": 1024,
            }
        )
        
        # Create memory for the agent
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Initialize the LangChain agent
        return initialize_agent(
            tools, 
            bedrock_llm, 
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def __init__(self):
        # Use the factory pattern to initialize the agent lazily
        super().__init__(
            agent_factory=self.create_agent,
            preserve_history=True
        )


def main():
    # Create an instance of the agent
    example_agent = ExampleLangChainAgent().name("example_agent")
    
    # Set up the Chorus framework with our agent
    chorus = Chorus(
        agents=[example_agent],
        stop_conditions=[NoActivityStopper()]
    )
    
    # Start the Chorus system
    chorus.start()
    
    # Send test messages to the agent
    print("\nSending message: What's the weather in New York?")
    msg1 = chorus.send_and_wait(
        destination=example_agent.identifier(),
        message="What's the weather in New York?"
    )
    print(f"Response: {msg1.content}")
    
    # Follow-up message that references the first one
    print("\nSending follow-up message: And what about in San Francisco?")
    msg2 = chorus.send_and_wait(
        destination=example_agent.identifier(),
        message="And what about in San Francisco?"
    )
    print(f"Response: {msg2.content}")
    
    # Try a more complex question
    print("\nSending message: What's the time difference between New York and Tokyo?")
    msg3 = chorus.send_and_wait(
        destination=example_agent.identifier(),
        message="What's the time difference between New York and Tokyo?"
    )
    print(f"Response: {msg3.content}")
    
    # Clean shutdown
    chorus.stop()

if __name__ == "__main__":
    main() 