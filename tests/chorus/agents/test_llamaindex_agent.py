import dotenv
from unittest.mock import MagicMock
from llama_index.core.base.llms.types import ChatMessage, ChatResponse
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from chorus.data import Message
from chorus.agents import LlamaIndexAgent

def mock_chat(input_chat):
    if len(input_chat) == 2:
        return ChatResponse(
            message=ChatMessage(content="""
Thought: The current language of the user is: English. I need to use a tool to help me answer this simple addition question.

Action: add
Action Input: {"a": 5, "b": 3}

Observation: 8

Thought: I can answer without using any more tools. I'll use the user's language to answer.

Answer: The result of 5 + 3 is 8.
    """, role="assistant")
        )
    else:
        return ChatResponse(
            message=ChatMessage(content="""
Thought: I can answer without using any more tools. I'll use the user's language to answer.
Answer: The result of 5 + 3 is 8.
    """, role="assistant")
        )

def test_llama_index_agent():
    """
    Test the LlamaIndexAgent by creating an instance, adding a message, and verifying that the response is not empty.
    """
    llm = MagicMock()
    llm.chat = mock_chat
    #llm = Bedrock(model="us.anthropic.claude-3-5-sonnet-20240620-v1:0")

    # Load environment variables from .env file
    dotenv.load_dotenv()

    # Define the 'add' tool
    def add(a: int, b: int) -> int:
        """Adds two numbers together."""
        return a + b

    # List of tools the agent can use
    toolkit = [FunctionTool.from_defaults(add)]

    # Set up conversational memory
    chat_memory_buffer = ChatMemoryBuffer.from_defaults()

    # Create the agent with the language model, tools, and memory
    agent = LlamaIndexAgent(
        name="Llama",
        llamaindexAgent=ReActAgent.from_tools(
            tools=toolkit,
            llm=llm,
            memory=chat_memory_buffer,
            verbose=True,
        )
    )

    context = agent.init_context()
    state = agent.init_state()
    response = agent.respond(context, state, Message(source="human", destination="Llama", content="What is 5+3?"))
    assert response is not None