---
title: Collaboration Patterns
description: Learn about multi-agent collaboration patterns in Chorus
---

# Multi-Agent Collaboration in Chorus

Chorus provides an extremely flexible multi-agent collaboration (MAC) framework and a powerful collaboration engine that allows you to team up your existing agents or new agents for solving complex problems. The core value you will get from Chorus is mainly on the collaboration aspect:

1. A robust collaboration environment that supports a large number of autonomous agents
2. A rich set of inter-agent communication and collaboration mechanisms such as team-level shared storage, communication channels, etc.
3. A flexible agent protocol allowing you to customize your own agent behavior at will

**All agents are autonomous** In Chorus, we treat all agents as autonomous entities that control their own behaviors. An agent in Chorus doesn't need to be reactive, that is, act only when it receives a message from the user or another agent. Instead, an agent can decide to explore files in the shared storage, or communicate with other agents whenever needed.

## Chorus's collaboration engine

To give each agent full autonomy, Chorus gives each agent a dedicated process so that the agents won't be blocked by other events. Chorus manages and optimizes the context synchronization between agents so that different agents can communicate and collaborate smoothly. This also means that your multi-agent solution on Chorus will be fully distributed and scalable. Chorus can potentially support hundreds of agents running in parallel on a single machine. In the future, Chorus will also support cross-node collaboration for large-scale multi-agent systems.

## Event-driven collaboration

Agents, teams or utility services, all entities in Chorus exchange information with each other by passing events or messages. Agents can subscribe and react to certain types of events. For example, an agent can subscribe to the team's shared storage so that it will be notified when a new file is created.

## Collaboration Patterns

Chorus supports various collaboration patterns to suit different use cases:

### Centralized Collaboration

In this pattern, a coordinator agent manages the workflow and delegates tasks to specialized agents:

```python
from chorus.collaboration import CentralizedCollaboration

# Create a centralized collaboration with a coordinator
collaboration = CentralizedCollaboration(
    coordinator="CoordinatorAgent"
)

# Assign the collaboration to a team
team = Team(
    name="AnalysisTeam",
    agents=[coordinator_agent, research_agent, analysis_agent],
    collaboration=collaboration
)
```

### Decentralized Collaboration

In this pattern, agents communicate directly with each other without a central coordinator:

```python
from chorus.collaboration import DecentralizedCollaboration

# Create a decentralized collaboration
collaboration = DecentralizedCollaboration()

# Assign the collaboration to a team
team = Team(
    name="ResearchTeam",
    agents=[agent1, agent2, agent3],
    collaboration=collaboration
)
```

## Building multi-agent solutions with Chorus

Building multi-agent solutions with Chorus is easy. You can start by going through our tutorials, which provide step-by-step guidance and examples. In general, we provide two ways for you to build your multi-agent solutions: 1) Develop with descriptive language (JSONnet) and 2) Develop with code (Python).

For simple multi-agent solutions, we recommend you use the declarative way by writing a small JSONnet file. JSONnet is a terse and expressive language that allows you to configure your multi-agent solution in a very intuitive way. For more complex use cases, you can customize your own agents, collaboration mechanisms, etc. by writing Python code. 