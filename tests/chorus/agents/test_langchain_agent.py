from chorus.data import Message
from chorus.agents.langchain_agent import LangChainAgent
from chorus.core import Chorus
from chorus.helpers.communication import CommunicationHelper
from langchain_community.tools import Tool
from langchain_aws.chat_models.bedrock import ChatBedrock
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
import pytest
import boto3
import os

def calculator(expression: str) -> str:
    """A simple calculator that evaluates mathematical expressions.
    
    Args:
        expression: A string containing a mathematical expression
        
    Returns:
        The result of evaluating the expression
        
    Example:
        >>> calculator("2 * 3 + 4")
        '10'
    """
    try:
        # Using eval is generally not recommended in production code
        # This is just for demonstration purposes
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

instruction = """
You are a math assistant that helps users solve mathematical calculations. You can perform basic arithmetic operations, 
as well as more complex mathematical calculations. Please show your work and explain the steps when solving problems.
"""

def test_basic_langchain_agent():
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'  # or your preferred region
    )

    llm = ChatBedrock(
        model_id="us.anthropic.claude-3-5-sonnet-20240620-v1:0",  # or your preferred model
        client=bedrock_client,
        model_kwargs={
            "temperature": 0,
            "max_tokens": 500,
        }
    )
    
    # Define our own calculator tool
    tool = Tool(
        name="calculator",
        func=calculator,
        description="Useful for performing mathematical calculations. Input should be a mathematical expression (e.g. '2 * 3 + 4')"
    )
    agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION
    # Initialize default tools
    memory = ConversationBufferMemory(memory_key="chat_history")

    langchain_agent = initialize_agent(
            tools=[tool],
            llm=llm,
            agent=agent_type,
            memory=memory,
            verbose=True,
            agent_kwargs={"system_message": instruction}
        )

    agent = LangChainAgent(
        name="MyLangChainAgent",
        langchain_agent=langchain_agent,
    )

    chorus = Chorus(agents=[agent])
    chorus.start()

    comm = CommunicationHelper(chorus.get_global_context())
    
    # Send message through message service
    test_expression = "(15 * 27) + (45 / 3)"
    expected_result = int(eval(test_expression))  # 420
    response = comm.send_and_wait(
        destination="MyLangChainAgent",
        content=f"What is the result of {test_expression}?"
    )
    
    # Verify expected result in the response
    assert expected_result in response.content, f"Expected result {expected_result} not found in agent's response: {response.content}"

    # Send a follow-up question referencing the previous calculation
    follow_up_response = comm.send_and_wait(
        destination="MyLangChainAgent", 
        content="If we take the previous result and multiply it by 2, what do we get?"
    )

    # The expected result should be 420 * 2 = 840
    expected_follow_up = 840
    assert str(expected_follow_up) in follow_up_response.content, f"Expected result {expected_follow_up} not found in agent's response: {follow_up_response.content}"

    chorus.stop()

if __name__ == '__main__':
    pytest.main([__file__])