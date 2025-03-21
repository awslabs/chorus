---
title: Chorus - Advanced Multi-Agent Collaboration
---

Build powerful multi-agent systems with Chorus, the open source framework for advanced multi-agent collaboration with autonomous agents. {% .lead %}

{% quick-links %}

{% quick-link title="Getting Started" icon="installation" href="/" description="Step-by-step guides to setting up Chorus and building your first multi-agent system." /%}

{% quick-link title="Architecture Guide" icon="presets" href="/" description="Learn how Chorus works internally and how to contribute to the project." /%}

{% quick-link title="Examples" icon="plugins" href="/" description="Explore sample applications and use cases built with Chorus." /%}

{% quick-link title="API Reference" icon="theming" href="/" description="Comprehensive documentation of Chorus APIs and components." /%}

{% /quick-links %}

## What is Chorus?

Chorus is a generalizable framework for collaborating with and orchestrating teams of autonomous agents. It focuses on the collaboration layer, simplifies the development and scaling of agent teams, and facilitates seamless collaboration between agents.

---

## Quick Reference

Explore major collaboration patterns to jump-start your multi-agent systems:

{% reference-grid /%}

---

## Core Value Proposition

Chorus provides a comprehensive framework focused on solving the collaboration problem, enabling developers to prototype and perfect multi-agent solutions with maximum flexibility for agent autonomy and behavior.

### Flexible Collaboration Mechanisms

Developers and researchers can prototype customized collaboration mechanisms using Chorus. They can leverage built-in collaboration utilities such as shared storage, scratchpads, agent recruiting, voting mechanisms, or customize the collaboration logic.

```python
# Example: Creating a collaborative agent team
from chorus.core import Chorus
from chorus.agents import TaskCoordinatorAgent, ConversationalTaskAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.workspace import NoActivityStopper

# Create specialized agents
coordinator_agent = TaskCoordinatorAgent(
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

### Execution Environment

Chorus provides an execution environment for teams of autonomous agents to collaborate and be optimized over time. Developers can debug their solutions easily with Chorus.

{% callout type="info" title="Key Differentiators" %}
Chorus focuses on solving the collaboration problem with multiple agents. While other frameworks try to be all-encompassing solutions, Chorus specializes in enabling effective agent collaboration through three key aspects:
- Distributed autonomous agents for enabling complex collaboration patterns
- Highly customizable collaboration logic with heterogeneous agents
- Built-in utilities for enhanced group collaboration
{% /callout %}

---

## Distributed Autonomous Agents

Agents in Chorus function as distributed autonomous entities with persistent lifespans, enabling them to independently manage their schedules, behaviors, and state. Through repeated interactions, agent teams can accumulate knowledge and refine their collaborative capabilities.

### Building Effective Teams

Chorus encourages developers to focus on assembling effective teams of specialized agents rather than designing rigid workflows, leading to more flexible and adaptable solutions.

```python
# Example: Defining agent specializations
from chorus.agents import ConversationalTaskAgent
from chorus.toolbox import WebRetrieverTool, DuckDuckGoWebSearchTool

# Create specialized agents with different capabilities
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
```

### Heterogeneous Agent Support

Chorus provides native support for seamless collaboration between heterogeneous agents, such as Bedrock Agents, Langchain agents, OpenAI Assistant agents, and more. As an open framework, Chorus empowers agents with the flexibility to define their own triggering conditions and orchestration logic.

{% callout type="warning" title="Flexibility vs. Complexity" %}
With great flexibility comes the need for thoughtful design. While Chorus allows for highly customizable agent interactions, it's important to design your multi-agent systems with clear communication protocols and well-defined responsibilities.
{% /callout %}

---

## Enhanced Group Collaboration

Chorus enhances group synergy through comprehensive built-in collaboration utilities. The framework enables concurrent task execution with real-time coordination, allowing specialized agents to work simultaneously on different aspects of a problem.

### Collaboration Utilities

The framework includes comprehensive utilities that enable agents to maintain state, dynamically toggle their availability, and scale horizontally through agent instance forking - all essential capabilities for building sophisticated multi-agent solutions.

### Getting Help

Join our community to get help with Chorus and contribute to its development.

{% quick-links %}

{% quick-link title="GitHub Repository" icon="installation" href="https://github.com/awslabs/chorus" description="Star the repository, report issues, and contribute to the codebase." /%}

{% quick-link title="Documentation" icon="presets" href="/" description="Read the comprehensive documentation to learn all about Chorus." /%}

{% quick-link title="Community Forum" icon="plugins" href="/" description="Join the discussion, ask questions, and share your projects." /%}

{% quick-link title="Discord Channel" icon="theming" href="/" description="Chat with other Chorus users and the development team." /%}

{% /quick-links %}
