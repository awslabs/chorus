from chorus.data import Message
from chorus.agents.langchain_agent import LangChainAgent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import Tool
from langchain_aws.chat_models.bedrock import ChatBedrock
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
import pytest
import boto3

instruction = """
You are an agent helping to suggest a good trip location close to the location the user provided for this weekend. Please suggest the location based on weather, safety, experience and budget.
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
            "temperature": 0.7,
            "max_tokens": 500,
        }
    )
    search = DuckDuckGoSearchRun()
    tool = Tool(
                name="web_search",
                func=search.run,
                description="Useful for searching information on the internet"
            )
    agent_type =  AgentType.ZERO_SHOT_REACT_DESCRIPTION
        # Initialize default tools
    memory = ConversationBufferMemory(memory_key="chat_history")

    agent = initialize_agent(
            tools=[tool],
            llm=llm,
            agent=agent_type,
            memory=memory,
            verbose=True
        ) 

    lang_chain_web_search_agent = LangChainAgent(
        name="BasicLangChainAgent",
        langchainAgent=agent
    )

    context = lang_chain_web_search_agent.init_context()
    state = lang_chain_web_search_agent.init_state()
    response = lang_chain_web_search_agent.respond(context, state, Message(source="human", destination="BasicLangChainAgent", content="Recommend a place to go for this weekend around New York"))
    assert response is not None

if __name__ == '__main__':
    pytest.main([__file__])