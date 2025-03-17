---
title: Workspace Management
description: Learn about workspace management in Chorus
---

# Workspace Management

A workspace is a top-level container that represents the overall solution. A workspace is the executable unit that a developer can run, version, and share. Users interact with it to instantiate agents and teams. A workspace consists of:

1. Teams
2. Agents
3. Workspace properties
4. Collaboration properties 

## Workspace Properties

Following is a full list of workspace properties that can be set by the user:

| Property Name     | Type                                                 | Description                                                                                 |
|-------------------|------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `title`           | string                                               | The title of the workspace.                                                                 |
| `description`     | string                                               | The description of the workspace.                                                           |
| `agents`          | list of agents                                       | The agents in the workspace.                                                                |
| `teams`           | list of teams                                        | The teams in the workspace.                                                                 |
| `main_channel`    | (optional) string                                    | The main channel that the user of the workspace will use to give requests and instructions. |
| `start_messages`  | (optional) list of `Message` objects                 | Pre-filled messages that should exist when a session starts.                                |
| `stop_conditions` | (optional) list of `MultiAgentStopCondition` objects | The stop conditions of the workspace.                                                       |

## Example Workspace

Following is an example workspace configuration for creating a simple multi-agent team for answering user's questions about artificial intelligence and machine learning:

```python
from chorus.core import Chorus
from chorus.agents import SynchronizedCoordinatorAgent, ToolChatAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.toolbox import DuckDuckGoWebSearchTool, WebRetrieverTool
from chorus.workspace import NoActivityStopper

# Create agents
coordinator_agent = SynchronizedCoordinatorAgent(
    "CoordinatorAgent",
    instruction="""
        Do not do any task by yourself, always try to call other agents.
        If there is no relevant agent available, tell the user that you do not have a agent to answer the question.
    """,
    reachable_agents={
        "NewsAgent": "An agent that can help user to find news related to artificial intelligence and summarize them by search web and access pages.",
        "KnowledgeAgent": "An agent that can help user to answer general questions about artificial intelligence and machine learning."
    }
)

news_agent = ToolChatAgent(
    "NewsAgent",
    instruction="You can help user to find news and summarize them by search web and access pages.",
    tools=[
        DuckDuckGoWebSearchTool(),
        WebRetrieverTool()
    ]
)

knowledge_agent = ToolChatAgent(
    "KnowledgeAgent",
    instruction="Help user to answer general questions about artificial intelligence and machine learning."
)

# Create a team
team = Team(
    name="DefaultTeam",
    agents=[coordinator_agent, news_agent, knowledge_agent],
    collaboration=CentralizedCollaboration(
        coordinator=coordinator_agent.get_name()
    )
)

# Initialize Chorus with the team
chorus = Chorus(
    teams=[team],
    stop_conditions=[NoActivityStopper()]
)

# Run the workspace
chorus.run()
```

## Workspace Management

Chorus provides several ways to manage workspaces:

### 1. Starting and Stopping

You can start and stop a workspace using the `run()` and `stop()` methods:

```python
# Start the workspace
chorus.run()

# Stop the workspace
chorus.stop()
```

### 2. Monitoring

You can monitor the activity in a workspace by subscribing to events:

```python
def message_handler(message):
    print(f"Message from {message.source} to {message.destination}: {message.content}")

chorus.get_environment().add_message_listener(message_handler)
```

### 3. Persistence

Workspaces can be saved and loaded for persistence:

```python
# Save workspace state
chorus.save_state("workspace_state.json")

# Load workspace state
chorus = Chorus.load_state("workspace_state.json")
```

## Best Practices

1. **Clear Organization**: Group related agents into teams
2. **Appropriate Stop Conditions**: Define when the workspace should stop running
3. **Error Handling**: Implement proper error handling for robustness
4. **Resource Management**: Monitor and manage resource usage for large workspaces 