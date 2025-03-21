---
title: Question Answering Team
nextjs:
  metadata:
    title: Question Answering Team
    description: Building a specialized question answering team with Chorus.
---

# Question Answering Team

This example demonstrates how to create a specialized question answering team using Chorus. The team consists of multiple agents working together to provide comprehensive answers to user questions.

## Team Structure

The question answering team consists of several specialized agents:

1. **Coordinator Agent**: Manages the overall question answering process
   - Analyzes incoming questions
   - Delegates research tasks to appropriate agents
   - Synthesizes final answers from agent contributions

2. **Research Agent**: Gathers factual information
   - Uses web search tools to find relevant information
   - Accesses and summarizes web pages
   - Provides citations and sources

3. **Knowledge Agent**: Provides domain expertise
   - Answers general questions based on its knowledge
   - Explains complex concepts in simple terms
   - Ensures accuracy of information

## Implementation Example

Here's how you can implement a question answering team with Chorus:

```python
from chorus.core import Chorus
from chorus.agents import TaskCoordinatorAgent, ConversationalTaskAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.workspace import NoActivityStopper
from chorus.toolbox import WebRetrieverTool, DuckDuckGoWebSearchTool

# Create specialized agents
coordinator_agent = TaskCoordinatorAgent(
    "FitnessAnsweringAgent",
    instruction="""
    Do not do any task by yourself, always try to call other agents.
    If there is no relevant agent available, tell the user that you do not have an agent to answer the question.
    Make your answer comprehensive and detailed.
    """,
    reachable_agents={
        "FactResearchAgent": "An agent that can help user to find facts related to fitness and summarize them by search web and access pages.",
        "KnowledgeAgent": "An agent that can help user to answer general questions about fitness." 
    }
)

fact_research_agent = ConversationalTaskAgent(
    "FactResearchAgent",
    instruction="You can help user to find facts related to fitness and summarize them by search web and access pages.",
    tools=[
        DuckDuckGoWebSearchTool(),
        WebRetrieverTool()
    ]
)

knowledge_agent = ConversationalTaskAgent(
    "KnowledgeAgent",
    instruction="Help user to answer general questions about fitness, nutrition, exercise and healthy lifestyle.",
)

# Form a collaborative team with centralized collaboration
team = Team(
    name="FitnessTeam",
    agents=[coordinator_agent, fact_research_agent, knowledge_agent],
    collaboration=CentralizedCollaboration(
        coordinator=coordinator_agent.get_name()
    )
)

# Initialize Chorus with the team
chorus = Chorus(
    teams=[team],
    stop_conditions=[NoActivityStopper()]
)

# Send a message to the team and run the collaboration
chorus.get_environment().send_message(
    source="human",
    destination=team.get_identifier(),
    content="What are the best parks in New York City for running?"
)
chorus.run()
```

## Key Features

1. **Centralized Coordination**: The coordinator agent manages the workflow
2. **Specialized Agents**: Each agent has a specific role and expertise
3. **Tool Integration**: Research agents use web search and retrieval tools
4. **Flexible Collaboration**: The team can handle a wide range of questions
5. **Automatic Delegation**: Questions are routed to the most appropriate agent

## Best Practices

1. **Clear Instructions**: Each agent has specific, focused responsibilities
2. **Tool Selection**: Provide appropriate tools based on agent roles
3. **Coordinator Design**: The coordinator should know when to delegate vs. answer directly
4. **Error Handling**: Include fallback mechanisms when agents can't answer
5. **Response Synthesis**: Combine information from multiple agents into coherent answers

## Running the Example

You can run this example with:

```bash
python examples/python/question_answering_team.py
```

The script will:
1. Initialize the team of specialized agents
2. Process the user's question
3. Delegate research tasks as needed
4. Synthesize a comprehensive answer
5. Return the final response to the user 