---
title: Centralized Collaboration
nextjs:
  metadata:
    title: Centralized Collaboration
    description: Implementing centralized collaboration patterns with a coordinator agent in Chorus.
---

# Centralized Collaboration

This example demonstrates how to implement a centralized collaboration pattern in Chorus, where a coordinator agent manages the workflow and delegates tasks to specialized agents.

## Overview

Centralized collaboration is one of the most common patterns for multi-agent systems. In this pattern, a coordinator agent serves as the central hub for communication and task delegation. The coordinator receives user requests, determines which specialized agents to call, and synthesizes the final response.

## Implementation Example

Here's how you can implement centralized collaboration in Chorus:

```python
from chorus.core import Chorus
from chorus.agents import SynchronizedCoordinatorAgent, ToolChatAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.workspace import NoActivityStopper

# Create a coordinator agent
coordinator_agent = SynchronizedCoordinatorAgent(
    "CoordinatorAgent",
    instruction="""
    You are the coordinator of a specialized team. Your job is to:
    1. Analyze the user's request
    2. Delegate tasks to the appropriate specialized agents
    3. Synthesize the final response
    
    Do not perform specialized tasks yourself. Always delegate to the appropriate agent.
    """,
    reachable_agents={
        "DataAnalysisAgent": "An agent that can analyze data and generate insights",
        "VisualizationAgent": "An agent that can create data visualizations",
        "ReportingAgent": "An agent that can generate comprehensive reports"
    }
)

# Create specialized agents
data_analysis_agent = ToolChatAgent(
    "DataAnalysisAgent",
    instruction="You are a data analysis agent specialized in analyzing data and generating insights."
)

visualization_agent = ToolChatAgent(
    "VisualizationAgent",
    instruction="You are a visualization agent specialized in creating data visualizations."
)

reporting_agent = ToolChatAgent(
    "ReportingAgent",
    instruction="You are a reporting agent specialized in generating comprehensive reports."
)

# Form a team with centralized collaboration
team = Team(
    name="DataTeam",
    agents=[coordinator_agent, data_analysis_agent, visualization_agent, reporting_agent],
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
    content="I need a comprehensive analysis of our Q2 sales data with visualizations."
)
chorus.run()
```

## How Centralized Collaboration Works

1. **User Request**: The user sends a request to the team
2. **Coordinator Analysis**: The coordinator agent analyzes the request
3. **Task Delegation**: The coordinator delegates specific tasks to specialized agents
4. **Parallel Execution**: Specialized agents work on their assigned tasks
5. **Response Collection**: The coordinator collects responses from specialized agents
6. **Synthesis**: The coordinator synthesizes a comprehensive response
7. **Final Response**: The synthesized response is returned to the user

## Key Features

1. **Single Point of Control**: The coordinator manages the entire workflow
2. **Clear Delegation**: Tasks are explicitly assigned to specialized agents
3. **Efficient Communication**: Reduced communication overhead compared to decentralized approaches
4. **Simplified Orchestration**: The coordinator handles all orchestration logic
5. **Predictable Workflow**: The collaboration follows a well-defined pattern

## Best Practices

1. **Clear Coordinator Instructions**: Define the coordinator's responsibilities explicitly
2. **Proper Agent Registration**: Ensure all specialized agents are registered with the coordinator
3. **Task Boundaries**: Define clear boundaries between agent responsibilities
4. **Error Handling**: Implement fallback mechanisms when agents can't complete tasks
5. **Response Synthesis**: Train the coordinator to effectively combine information from multiple agents

## Advantages and Limitations

### Advantages
- Simpler to implement and reason about
- Clear chain of command and responsibility
- Easier to debug and monitor
- Reduced communication overhead
- Well-suited for hierarchical tasks

### Limitations
- Single point of failure (the coordinator)
- Potential bottleneck at the coordinator
- Less flexible than decentralized approaches
- May not scale as well with many agents
- Limited agent autonomy

## When to Use Centralized Collaboration

Centralized collaboration is ideal for:
- Tasks with clear hierarchical structure
- Workflows requiring careful orchestration
- Systems with a moderate number of agents
- Applications where predictability is important
- Scenarios where a single agent needs oversight of the entire process
