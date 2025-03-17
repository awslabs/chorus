---
title: Hello World with Chorus
nextjs:
  metadata:
    title: Hello World with Chorus
    description: Build your first multi-agent system with Chorus in just a few minutes.
---

# Hello World with Chorus

This tutorial will guide you through creating your first multi-agent system using Chorus. We'll build a simple team of agents that can answer questions about fitness by collaborating with each other.

---

## Prerequisites

Before you begin, make sure you've:

- [Installed Chorus](/docs/installation) on your system
- Basic understanding of Python
- A text editor or IDE of your choice

## Step 1: Understanding the Project Structure

In this Hello World example, we'll create a team with three agents:

1. **Coordinator Agent**: Manages the workflow and delegates tasks to specialized agents
2. **Fact Research Agent**: Searches the web to find fitness-related information
3. **Knowledge Agent**: Answers general questions about fitness

Together, these agents will collaborate to provide detailed answers to fitness-related questions.

## Step 2: Importing the Required Modules

Create a new file named `hello_world.py` and add the following imports:

```python
from chorus.core import Chorus

from chorus.agents import SynchronizedCoordinatorAgent, ToolChatAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration

from chorus.toolbox import WebRetrieverTool
from chorus.toolbox import DuckDuckGoWebSearchTool

from chorus.workspace import NoActivityStopper
```

These imports provide all the components we need:
- Core Chorus functionality
- Agent types for coordination and tool usage
- Team and collaboration structures
- Web search and retrieval tools
- A condition to stop the execution when there's no more activity

## Step 3: Creating the Agents

Next, let's create our three agents:

```python
# Create the coordinator agent that will manage the workflow
coordinator_agent = SynchronizedCoordinatorAgent(
    "FitnessAnsweringAgent",
    instruction="""
    Do not do any task by yourself, always try to call other agents.
    If there is no relevant agent available, tell the user that you do not have a agent to answer the question.
    Make your answer comprehensive and detailed.
    """,
    reachable_agents={
        "FactResearchAgent": "An agent that can help user to find facts related to fitness and summarize them by search web and access pages.",
        "KnowledgeAgent": "An agent that can help user to answer general questions about fitness." 
    }
)

# Create the fact research agent with web search capabilities
fact_research_agent = ToolChatAgent(
    "FactResearchAgent",
    instruction="You can help user to find facts related to fitness and summarize them by search web and access pages.",
    tools=[
        DuckDuckGoWebSearchTool(),
        WebRetrieverTool()
    ]
)

# Create the knowledge agent for fitness expertise
knowledge_agent = ToolChatAgent(
    "KnowledgeAgent",
    instruction="Help user to answer general questions about fitness, nutrition, exercise and healthy lifestyle.",
)
```

Notice how each agent has:
- A unique name identifier
- Clear instructions about its role
- The coordinator knows which agents it can reach out to
- The fact research agent has specific tools for web search and retrieval

## Step 4: Forming a Team

Now that we have our agents, let's form them into a team:

```python
team = Team(
    name="HelloWorldTeam",
    agents=[coordinator_agent, fact_research_agent, knowledge_agent],
    collaboration=CentralizedCollaboration(
        coordinator=coordinator_agent.get_name()
    )
)
```

This creates a team named "HelloWorldTeam" with our three agents. We're using a centralized collaboration pattern, where the coordinator agent manages the interaction between all team members.

## Step 5: Setting Up Chorus

Next, let's initialize Chorus with our team:

```python
chorus = Chorus(
    teams=[team],
    stop_conditions=[NoActivityStopper()]
)
```

This creates a Chorus instance with our team and specifies that the execution should stop when there's no more activity among the agents.

## Step 6: Running the Agents

Finally, let's send a message to the team and run the collaboration:

```python
chorus.get_environment().send_message(
    source="human",
    destination=team.get_identifier(),
    content="What are the best parks in New York City for running?"
)
chorus.run()
```

This sends a question about running parks in New York City to the team and starts the execution. The agents will collaborate to provide an answer.

## Complete Code

Here's the complete Hello World example:

```python
from chorus.core import Chorus

from chorus.agents import SynchronizedCoordinatorAgent, ToolChatAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration

from chorus.toolbox import WebRetrieverTool
from chorus.toolbox import DuckDuckGoWebSearchTool

from chorus.workspace import NoActivityStopper


if __name__ == '__main__':
    coordinator_agent = SynchronizedCoordinatorAgent(
        "FitnessAnsweringAgent",
        instruction="""
        Do not do any task by yourself, always try to call other agents.
        If there is no relevant agent available, tell the user that you do not have a agent to answer the question.
        Make your answer comprehensive and detailed.
        """,
        reachable_agents={
            "FactResearchAgent": "An agent that can help user to find facts related to fitness and summarize them by search web and access pages.",
            "KnowledgeAgent": "An agent that can help user to answer general questions about fitness." 
        }
    )
    fact_research_agent = ToolChatAgent(
        "FactResearchAgent",
        instruction="You can help user to find facts related to fitness and summarize them by search web and access pages.",
        tools=[
            DuckDuckGoWebSearchTool(),
            WebRetrieverTool()
        ]
    )
    knowledge_agent = ToolChatAgent(
        "KnowledgeAgent",
        instruction="Help user to answer general questions about fitness, nutrition, exercise and healthy lifestyle.",
    )

    team = Team(
        name="HelloWorldTeam",
        agents=[coordinator_agent, fact_research_agent, knowledge_agent],
        collaboration=CentralizedCollaboration(
            coordinator=coordinator_agent.get_name()
        )
    )

    chorus = Chorus(
        teams=[team],
        stop_conditions=[NoActivityStopper()]
    )

    chorus.get_environment().send_message(
        source="human",
        destination=team.get_identifier(),
        content="What are the best parks in New York City for running?"
    )
    chorus.run()
```

## Step 7: Running the Example

Save the file as `hello_world.py` and run it with:

```bash
python hello_world.py
```

You'll see the agents collaborate in real-time to answer the question about running parks in New York City. The coordinator will delegate the task to the appropriate agents, who will then use their capabilities to provide information.

## How It Works

Here's what happens when you run this example:

1. The human message is sent to the team via the environment
2. The coordinator agent receives the message and analyzes the question
3. The coordinator determines that the fact research agent can help and delegates the task
4. The fact research agent uses its web search and retrieval tools to find information
5. The knowledge agent may contribute general fitness insights
6. The coordinator assembles the information into a comprehensive answer
7. The final response is provided to the user

This simple example demonstrates Chorus's key concepts:
- Agent specialization and division of labor
- Centralized collaboration pattern
- Tool usage for accessing external information
- Message-based communication

## Next Steps

Now that you've built your first multi-agent system with Chorus, you can:

1. [Explore different collaboration patterns](/docs/collaboration-patterns)
2. [Learn about tool-using agents](/docs/tool-using-agents)
3. [Understand agent communication](/docs/agent-communication)
4. [Build a more complex team](/docs/team-formation)

Congratulations on creating your first Chorus application! 