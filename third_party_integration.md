
# Overview

This document describes how to integrate with third-party libraries.

## LangChain Integration

Chorus provides optional integration with the [LangChain](https://github.com/langchain-ai/langchain) library through the `LangChainAgentAdapter` class. This allows you to use LangChain agents within the Chorus framework.

### Installation

To use the LangChain integration, you need to install the optional `langchain` dependencies:

```bash
pip install "chorus[langchain]"
```

### Using LangChainAgentAdapter

The `LangChainAgentAdapter` is designed to translate between Chorus's message interface and LangChain's agent interface.

To avoid pickling issues in distributed environments, we need to create the agent in a factory function:

```python
from chorus.agents import LangChainAgentAdapter
from chorus.agents.base import Agent
from langchain.agents import AgentType, initialize_agent
from langchain.tools import Tool

class MyLangChainAgent(LangChainAgentAdapter):
    @staticmethod
    def create_agent():
        # This function runs in the worker process, avoiding pickling issues
        tools = [
            Tool(
                name="Weather",
                func=lambda location: f"The weather in {location} is sunny.",
                description="Useful for getting the weather in a specific location",
            ),
        ]
        
        # Initialize the LLM - can have unpicklable objects like API clients
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(temperature=0)
        
        # Initialize LangChain agent
        return initialize_agent(
            tools, 
            llm, 
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True
        )
    
    def __init__(self):
        # Use the factory pattern for initialization
        super().__init__(
            agent_factory=self.create_agent,
            preserve_history=True
        )
```

## Examples

```bash
python examples/python/langchain_agent.py
```
