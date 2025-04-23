---
title: Chorus - Advanced Multi-Agent Collaboration
---

Build powerful multi-agent systems with Chorus, the open source framework for advanced multi-agent collaboration with autonomous agents. {% .lead %}

{% quick-links %}

{% quick-link title="Getting Started" icon="installation" href="/" description="Step-by-step guides to setting up Chorus and building your first multi-agent system." /%}

{% quick-link title="Concepts" icon="presets" href="/" description="Learn how Chorus works internally and how to contribute to the project." /%}

{% quick-link title="Examples" icon="plugins" href="/" description="Explore sample applications and use cases built with Chorus." /%}

{% quick-link title="API Reference" icon="theming" href="/" description="Comprehensive documentation of Chorus APIs and components." /%}

{% /quick-links %}

## What is Chorus?

Chorus is a generalizable framework for collaborating with and orchestrating teams of autonomous agents with advanced collaboration patterns. It focuses on the collaboration layer, simplifies the development and scaling of agent teams, and facilitates seamless collaboration between agents.

---

## Quick Reference

Explore major collaboration patterns to jump-start your multi-agent systems:

{% reference-grid /%}

---

## Core Value Proposition

Chorus provides a comprehensive framework focused on solving the collaboration problem, enabling developers to prototype and perfect multi-agent solutions with maximum flexibility for agent autonomy and behavior.

### Scaling up fully distributed multi-agent collaboration

Developers and researchers can prototype various collaboration mechanisms using Chorus with all agents running in a fully distributed manner. 

```python
# Example: Creating a collaborative agent team
from chorus.core import Chorus
from chorus.agents import TaskCoordinatorAgent, ConversationalTaskAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration

# Create specialized agents
coordinator_agent = TaskCoordinatorAgent(
    instruction="""
    Do not do any task by yourself, always try to call other agents.
    If there is no relevant agent available, tell the user that you do not have a agent to answer the question.
    Make your answer comprehensive and detailed.
    """,
    reachable_agents={
        "FactResearchAgent": "An agent that can help user to find facts related to fitness and summarize them by search web and access pages.",
        "KnowledgeAgent": "An agent that can help user to answer general questions about fitness." 
    }
).name("FitnessAnsweringAgent")

fact_research_agent = ConversationalTaskAgent(
    instruction="Find facts related to fitness and summarize them by search web and access pages.",
    tools=[
        DuckDuckGoWebSearchTool(),
        WebRetrieverTool()
    ]
).name("FactResearchAgent")

knowledge_agent = ConversationalTaskAgent(
    instruction="Answer general questions about fitness.",
).name("KnowledgeAgent")

# Form a collaborative team with centralized collaboration
team = Team(
    name="FitnessTeam",
    agents=[coordinator_agent, fact_research_agent, knowledge_agent],
    collaboration=CentralizedCollaboration(
        coordinator=coordinator_agent.get_name()
    )
)

# Initialize Chorus with the team
chorus = Chorus(teams=[team])
chorus.start()

# Send a message to the team and run the collaboration
response = chorus.send_and_wait(
    destination=team.identifier(),
    message="What are the best parks in New York City for running?"
)

print(response.content)
chorus.stop()
```

### Advanced agent-to-agent collaboration mechanisms

Chorus provides an optimized inter-agent communication and collaboration support. You can leverage built-in collaboration utilities such as shared storage, scratchpads, agent recruiting, voting mechanisms, or customize the collaboration logic.

{% callout type="info" title="Key Differentiators" %}
Chorus simplifies the development of collaboration mechanisms with a large number of agents. While other frameworks try to be all-encompassing solutions, Chorus focuses on building an effective agent collaboration layer through three key aspects:
- Fully distributed autonomous agents for enabling complex collaboration patterns
- Highly customizable collaboration logic with heterogeneous agents - out-of-the-box inter-operability
- Built-in utilities and toolboxesfor advanced collaboration patterns
{% /callout %}

### Heterogeneous Agent Support

Chorus provides native support for seamless collaboration between heterogeneous agents, such as Langchain agents, LlamaIndex agents, and more. As an open framework, Chorus empowers agents with the flexibility to define their own triggering conditions and orchestration logic.

---

## Distributed Autonomous Agents

Agents in Chorus function as distributed autonomous entities with persistent lifespans, enabling them to independently manage their schedules, behaviors, and state. Through repeated interactions, agent teams can accumulate knowledge and refine their collaborative capabilities.

### Building Effective Teams

Chorus encourages developers to focus on assembling effective teams of specialized agents rather than designing rigid graph-alike workflows, leading to more flexible and adaptable solutions. For example, Chorus supports context-aware agents using a trigger system. Agents can dynamically switch behavior based on message conditions:

```python
# Create agent with base instruction
agent = ConversationalTaskAgent(
    instruction="Default behavior when no triggers match"
).name("SupportAgent")

# Create contexts for different scenarios
technical_context = OrchestrationContext(
    agent_instruction="You are a technical support specialist who helps with code issues"
)

billing_context = OrchestrationContext(
    agent_instruction="You are a billing support specialist who helps with account charges"
)

# Register triggers to automatically switch contexts based on message properties
agent.on(MessageTrigger(source="TechnicalTeam"), technical_context)
agent.on(MessageTrigger(source="BillingTeam"), billing_context)
agent.on(MessageTrigger(channel="billing-channel"), billing_context)
```


### Multi-agent reflection and optimization

Ultimately, Chorus enables multi-agent systems to engage in collective reflection and optimization processes. Teams of agents can evaluate their past trajectroies, identify bottlenecks, and adjust their collaboration strategies for better collaboraiton in the future. This optimization capability allows agent systems to evolve over time, becoming more efficient and effective at solving complex problems through continuous learning and adaptation.

---

## Advanced Group Collaboration

Chorus enhances group synergy through comprehensive built-in collaboration utilities. The framework enables concurrent task execution with real-time coordination, allowing specialized agents to work simultaneously on different aspects of a problem.

### Collaboration Utilities

The framework includes comprehensive utilities that enable agents to maintain state, dynamically toggle their availability, and scale horizontally through agent instance forking - all essential capabilities for building sophisticated multi-agent solutions. 


### Getting Help

Join our community to get help with Chorus and contribute to its development.

{% quick-links %}

{% quick-link title="GitHub Repository" icon="installation" href="https://github.com/awslabs/chorus" description="Star the repository, report issues, and contribute to the codebase." /%}

{% quick-link title="Documentation" icon="presets" href="/" description="Read the comprehensive documentation to learn all about Chorus." /%}

{% /quick-links %}
