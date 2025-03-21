---
title: Team Formation
description: Learn about team formation in Chorus
---

# Teams

An agent team holds a group of agents who work together for a common goal, which is the most granular collaboration unit. On a high level, a team consists of:

1. Member agents
2. Collaboration mechanism (e.g., decision making rules)
3. Services such as team toolbox and shared storage

## Team properties

A team has the following properties:

| Property Name   | Type                     | Description                                                             |
|-----------------|--------------------------|-------------------------------------------------------------------------|
| `name`          | string                   | The name of the team                                                    |
| `agents`        | list of agent names      | The IDs of the agents in the team                                       |
| `collaboration` | a `Collaboration` object | The collaboration mechanism that defines rules for team decision making |
| `services`      | a list of `Services` objects | A list of services provided by the team                                |

## Creating a Team

In Chorus, you can create a team by instantiating the `Team` class and providing the necessary properties:

```python
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.agents import ConversationalTaskAgent, TaskCoordinatorAgent

# Create agents
coordinator = TaskCoordinatorAgent(
    "TeamCoordinator",
    instruction="Coordinate the team to solve problems",
    reachable_agents={
        "Researcher": "Finds information through web search",
        "Analyst": "Analyzes data and provides insights"
    }
)

researcher = ConversationalTaskAgent(
    "Researcher",
    instruction="Find information through web search",
    tools=[WebSearchTool(), WebRetrieverTool()]
)

analyst = ConversationalTaskAgent(
    "Analyst",
    instruction="Analyze data and provide insights"
)

# Create a team with centralized collaboration
team = Team(
    name="ResearchTeam",
    agents=[coordinator, researcher, analyst],
    collaboration=CentralizedCollaboration(
        coordinator=coordinator.get_name()
    )
)
```

## Team Communication

Agents within a team can communicate with each other through messages. The team provides a communication channel that allows agents to send and receive messages:

```python
# Send a message to the team
chorus.get_environment().send_message(
    source="human",
    destination=team.get_identifier(),
    content="Research the impact of climate change on agriculture"
)
```

## Team Services

Teams can provide various services to their member agents, such as:

1. **Shared Storage**: A shared space where agents can store and retrieve information
2. **Team Toolbox**: A collection of tools that all team members can access
3. **Voting Mechanisms**: Services for collective decision making

These services enhance the collaboration capabilities of the team and allow agents to work together more effectively. 