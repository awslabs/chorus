# LlamaIndex Integration

Chorus provides integration with [LlamaIndex](https://www.llamaindex.ai/) through the `LlamaIndexAgentAdapter` class. This adapter allows you to use LlamaIndex agents within the Chorus framework.

## Installation

LlamaIndex is an optional dependency. To use it, you need to install Chorus with the `llamaindex` extra:

```bash
pip install chorus[llamaindex]
```

Or install the dependencies separately:

```bash
pip install llama-index llama-index-core
```

## Basic Usage

The `LlamaIndexAgentAdapter` allows you to wrap a LlamaIndex agent and use it within the Chorus framework. Here's a simple example:

```python
from chorus.agents import LlamaIndexAgentAdapter
from llama_index.agent import ReActAgent
from llama_index.llms.openai import OpenAI

class MyLlamaIndexAgent(LlamaIndexAgentAdapter):
    @staticmethod
    def create_agent():
        # Create a LlamaIndex agent
        llm = OpenAI(model="gpt-4")
        tools = [...]  # Your tools here
        agent = ReActAgent.from_tools(tools, llm=llm)
        return agent
    
    def __init__(self):
        super().__init__(
            agent_factory=self.create_agent,
            preserve_history=True
        )

# Use the agent in Chorus
agent = MyLlamaIndexAgent().name("llamaindex_agent")
chorus = Chorus(agents=[agent], ...)
chorus.start()
```

## AWS Bedrock Integration

For AWS Bedrock integration, you can use the `BedrockConverse` LLM:

```python
from chorus.agents import LlamaIndexAgentAdapter
from llama_index.llms.bedrock_converse import BedrockConverse

# Define a simple calculator agent
class SimpleCalculatorAgent:
    def __init__(self, llm):
        self.llm = llm
        # Define tools and other functionality
    
    def run(self, query):
        # Process the query using the LLM
        return self.llm.complete(prompt)

class BedrockAgent(LlamaIndexAgentAdapter):
    @staticmethod
    def create_agent():
        # Create Bedrock Converse LLM
        llm = BedrockConverse(
            model="anthropic.claude-3-haiku-20240307-v1:0",
            region_name="us-east-1",
            # Add AWS credentials as needed
        )
        
        # Create a simple agent
        return SimpleCalculatorAgent(llm)
    
    def __init__(self):
        super().__init__(
            agent_factory=self.create_agent,
            preserve_history=True
        )
```

## Supported Agent Types

The adapter supports various LlamaIndex agent interfaces:

1. Agents with a `run()` method (like `FunctionAgent`)
2. Agents with a `chat()` method (like `ReActAgent`)
3. Agents with `stream_chat()` or `query()` methods

The adapter automatically detects which interfaces are supported by the agent and uses the appropriate method.

## Agent Factory Pattern

The adapter uses a factory pattern to create agents. This is important because:

1. It allows lazy initialization of the agent
2. It avoids pickling issues with objects that can't be serialized
3. It ensures the agent is created in the worker process

Always create your agent in a static `create_agent()` method and use it in the constructor:

```python
@staticmethod
def create_agent():
    # Create and return the agent here
    return agent

def __init__(self):
    super().__init__(agent_factory=self.create_agent)
```

## History Preservation

The adapter can preserve conversation history between calls. This is enabled by default (`preserve_history=True`).

The history is stored in the agent's state and is used to provide context for future interactions.

## Handling Async Agents

The adapter automatically handles both synchronous and asynchronous agent interfaces. If an agent method is a coroutine function (async), the adapter will run it in an event loop. This enables compatibility with the latest versions of LlamaIndex which use async functions.

## Troubleshooting

If you encounter errors, check the following:

1. Make sure LlamaIndex is installed: `pip install chorus[llamaindex]`
2. Check which LlamaIndex versions are compatible with your agent
3. If you see event loop errors, try using a simple agent approach instead of complex workflows 