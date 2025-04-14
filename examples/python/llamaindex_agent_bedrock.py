"""
Example of using the LlamaIndexAgentAdapter with AWS Bedrock Converse.

This example demonstrates how to:
1. Use the BedrockConverse LLM from llama_index to interact with Claude
2. Create a simple agent with calculator tools
3. Wrap the agent with LlamaIndexAgentAdapter
4. Run it within the Chorus framework
"""

import logging
import os
from typing import Optional, List, Dict, Any, Callable

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure required packages are installed
try:
    # Import the LLM
    try:
        from llama_index.llms.bedrock_converse import BedrockConverse
        logger.info("Imported BedrockConverse from llama_index.llms.bedrock_converse")
    except ImportError:
        try:
            from llama_index.llms.bedrock import BedrockConverse
            logger.info("Imported BedrockConverse from llama_index.llms.bedrock")
        except ImportError:
            from llama_index_llms_bedrock_converse import BedrockConverse
            logger.info("Imported BedrockConverse from llama_index_llms_bedrock_converse")
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise ImportError("This example requires the following packages:\n"
                     "pip install llama-index\n"
                     "pip install llama-index-llms-bedrock-converse")

from chorus.core import Chorus
from chorus.agents import LlamaIndexAgentAdapter
from chorus.workspace import NoActivityStopper


# Define simple calculator functions for tools
def multiply(a: int, b: int) -> int:
    """Multiply two integers and returns the result integer"""
    return a * b


def add(a: int, b: int) -> int:
    """Add two integers and returns the result integer"""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a and return the result integer"""
    return a - b


def divide(a: int, b: int) -> float:
    """Divide a by b and return the result as a float"""
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b


# Define a custom class that will respond to the user's queries using the tools
class SimpleCalculatorAgent:
    """A simple calculator agent that uses tools directly without FunctionAgent."""

    def __init__(self, llm):
        self.llm = llm
        self.tools = {
            "multiply": multiply,
            "add": add,
            "subtract": subtract,
            "divide": divide,
        }
        
    def _get_tool_descriptions(self) -> str:
        """Create a string description of the available tools."""
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"{name}: {tool.__doc__}")
        return "\n".join(descriptions)
    
    def run(self, query: str) -> str:
        """Run the agent with the user's query."""
        # Create a prompt that describes the tools and asks the model to use them
        tool_descriptions = self._get_tool_descriptions()
        
        prompt = f"""You are a helpful calculator assistant that can perform basic math operations.
You have access to the following tools:

{tool_descriptions}

When solving problems, think step by step and break down complex calculations.
For example, to calculate (121 + 2) * 5:
1. First add 121 + 2 = 123
2. Then multiply 123 * 5 = 615

The user's question is: {query}

Solve this problem using the tools available. Show your work.
"""
        
        # Get the completion from the LLM
        try:
            response = self.llm.complete(prompt)
            return str(response)
        except Exception as e:
            logger.error(f"Error getting completion: {e}")
            return f"Error: {str(e)}"
    
    # Add dummy method for compatibility
    def chat(self, query: str, chat_history: Optional[List] = None) -> str:
        """Forward to run method for compatibility."""
        return self.run(query)


class CalculatorAgent(LlamaIndexAgentAdapter):
    @staticmethod
    def create_agent():
        """Create a SimpleCalculatorAgent with calculator tools."""
        # Create Bedrock Converse LLM
        llm = BedrockConverse(
            model="anthropic.claude-3-haiku-20240307-v1:0",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )
        
        # Log which model we're using
        logger.info(f"Using model: {llm.model}")
        
        # Create our simple agent (not FunctionAgent)
        agent = SimpleCalculatorAgent(llm)
        
        logger.info("SimpleCalculatorAgent created successfully")
        return agent
    
    def __init__(self):
        # Use the factory pattern to initialize the agent lazily
        super().__init__(
            agent_factory=self.create_agent,
            preserve_history=True
        )


def main():
    try:
        # Create an instance of the agent
        calculator_agent = CalculatorAgent().name("calculator_agent")
        logger.info(f"Created agent: {calculator_agent.identifier()}")
        
        # Set up the Chorus framework with our agent
        chorus = Chorus(
            agents=[calculator_agent],
            stop_conditions=[NoActivityStopper()]
        )
        
        # Start the Chorus system
        logger.info("Starting Chorus system")
        chorus.start()
        
        # Send test messages to the agent
        print("\nSending message: What is 42 + 17?")
        msg1 = chorus.send_and_wait(
            destination=calculator_agent.identifier(),
            message="What is 42 + 17?"
        )
        print(f"Response: {msg1.content}")
        
        print("\nSending message: What is (121 + 2) * 5?")
        msg2 = chorus.send_and_wait(
            destination=calculator_agent.identifier(),
            message="What is (121 + 2) * 5?"
        )
        print(f"Response: {msg2.content}")
        
        print("\nSending message: If I have 250 dollars and spend 75, then divide the remainder by 7, what do I get?")
        msg3 = chorus.send_and_wait(
            destination=calculator_agent.identifier(),
            message="If I have 250 dollars and spend 75, then divide the remainder by 7, what do I get?"
        )
        print(f"Response: {msg3.content}")
        
        # Clean shutdown
        chorus.stop()
    except Exception as e:
        logger.error(f"Error running example: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Ensure any created resources are cleaned up
        try:
            if 'chorus' in locals():
                chorus.stop()
        except:
            pass

if __name__ == "__main__":
    main() 