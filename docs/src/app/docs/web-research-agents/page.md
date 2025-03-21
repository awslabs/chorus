---
title: Web Research Agents
nextjs:
  metadata:
    title: Web Research Agents
    description: Building web research agents with asynchronous tool calling in Chorus.
---

# Web Research Agents with Async Tool Calling

This example demonstrates how to create web research agents that can asynchronously call tools to retrieve information from the web. This approach is particularly useful for research-intensive tasks where agents need to gather information from multiple sources.

## Overview

As a team service, `TeamToolbox` allows you to register a set of tools and make them available to all agents in the team. In this example, we'll show how to call the tools asynchronously from a member agent, which is particularly useful for web research tasks.

## Implementation Example

Here's how you can implement web research agents with asynchronous tool calling:

```python
from chorus.agents import ConversationalTaskAgent
from chorus.toolbox import ArxivRetrieverTool, WebRetrieverTool, DuckDuckGoWebSearchTool
from chorus.collaboration import CentralizedCollaboration
from chorus.teams import Team
from chorus.teams.services import TeamToolbox
from chorus.teams.toolbox import AsyncTeamToolClient

# Create research tools
arxiv_retriever_tool = ArxivRetrieverTool()
web_retriever_tool = WebRetrieverTool()
web_search_tool = DuckDuckGoWebSearchTool()

# Create a paper research agent with async tool access
paper_research_agent = ConversationalTaskAgent(
    name="PaperResearchAgent",
    tools=[
        AsyncTeamToolClient(arxiv_retriever_tool),
        AsyncTeamToolClient(web_retriever_tool),
        AsyncTeamToolClient(web_search_tool)
    ],
    instruction="You are a paper research agent that can help find academic papers on Arxiv and related information from the web."
)

# Create a general research agent
general_research_agent = ConversationalTaskAgent(
    name="GeneralResearchAgent",
    tools=[
        AsyncTeamToolClient(web_retriever_tool),
        AsyncTeamToolClient(web_search_tool)
    ],
    instruction="You are a general research agent that can help find information from the web."
)

# Create a coordinator agent
coordinator_agent = ConversationalTaskAgent(
    name="CoordinatorAgent",
    instruction="""
    You are the coordinator of a research team. Your job is to:
    1. Analyze the user's research request
    2. Delegate to the appropriate specialized agent
    3. Synthesize the final research report
    
    Do not perform research directly. Always delegate to the appropriate agent.
    """
)

# Form a research team with centralized collaboration
research_team = Team(
    name="ResearchTeam",
    agents=[coordinator_agent, paper_research_agent, general_research_agent],
    collaboration=CentralizedCollaboration(coordinator=coordinator_agent.get_name()),
    services=[TeamToolbox(
        tools=[arxiv_retriever_tool, web_retriever_tool, web_search_tool]
    )]
)
```

## Asynchronous Tool Calling Mechanism

When an agent calls a tool using the asynchronous client, an event with type `team_service` is sent to the team service process. The team toolbox executes the tool in a separate process without blocking the agent. Once the execution is complete, an observation message is sent back to the agent with the execution result.

This approach offers several advantages:
1. **Non-blocking operation**: Agents can continue processing while waiting for tool results
2. **Parallel tool execution**: Multiple tools can be called simultaneously
3. **Efficient resource usage**: Long-running tool operations don't block the entire system
4. **Improved responsiveness**: Agents can provide partial results while waiting for tools

## Key Features

1. **Asynchronous Tool Execution**: Tools run in separate processes without blocking agents
2. **Specialized Research Agents**: Different agents for different research domains
3. **Centralized Coordination**: Coordinator manages the research workflow
4. **Tool Sharing**: All tools are available to the entire team through TeamToolbox
5. **Flexible Research Capabilities**: Combine academic and web research in one system

## Best Practices

1. **Tool Selection**: Choose appropriate tools for each research domain
2. **Clear Agent Instructions**: Define specific research responsibilities
3. **Error Handling**: Implement fallbacks for when tools fail or timeout
4. **Result Synthesis**: Combine information from multiple sources coherently
5. **Timeout Management**: Set appropriate timeouts for asynchronous operations

## Running the Example

You can run this example with:

```bash
python examples/python/team_async_tool_calling.py
```

The script will:
1. Initialize the research team with specialized agents
2. Register the research tools with the team toolbox
3. Process research requests asynchronously
4. Demonstrate parallel tool execution
5. Show how to handle and synthesize results from multiple sources
