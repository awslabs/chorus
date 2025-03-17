---
title: Understanding Agents
description: Learn about agents in Chorus and how they work
---

# Agents

## Overview

An agent in Chorus is an autonomous entity capable of taking self-initiated actions and having full control over its behavior and state management. An agent can reason, plan, and execute multiple steps to solve complex problems. As an agent developer, you need to design each agent's behavior and assign agents to teams. To control an agent's behavior, there are several approaches in Chorus:

1. Leveraging existing agent classes (e.g., `ToolChatAgent`): You can provide natural language instructions to the agent to control its behavior.
2. Extending agent classes: This allows for full customization of the agent's behavior.

Chorus allows you to create fully customized heterogeneous agents. By following a basic design principle, these agents can run seamlessly and work with each other using Chorus's execution engine. We can see how to do this in the following sections.

## Base Agent Contract

All agents in Chorus follow a base contract, which decomposes an agent into three building blocks: 1) agent state, 2) agent context and 3) orchestration logic.

- **Agent State** Internal representation, managed by the agent.
- **Agent Context** A medium that the agent use to interact with the environment, managed by Chorus
- **Orchestration Logic** Logic that determines the agent's behavior.

Both the agent state and agent context are scoped to a session. The orchestration logic fully controls an agent's behavior. It determines when and how to interact with environment through the agent context, and how to manage and update the agent state.

### An Example Agent
The following code snippet shows how to create an agent that sends a message to `human` every 10 seconds.

```python
from chorus.agents import Agent
from chorus.data import AgentState, AgentContext, Message
import time


class TestAgentState(AgentState):
    last_message_timestamp = 0


class TestAgent(Agent):

    def init_state(self) -> TestAgentState:
        return TestAgentState()

    def iterate(self, context: AgentContext, state: AgentState) -> Optional[AgentState]:
        current_time = time.time()
        if current_time - state.last_message_timestamp > 10:
            context.message_service.send_message(Message(destination="human", content="Hello."))
            state.last_message_timestamp = current_time
        return state
```

### Passive Agents

By default, all agents are autonomous and active in Chorus. The orchestration logic defined through the `iterate` function, which will be triggered recurrently with a fixed frequency. In many cases, we may want to create agents that only passively reacts to an event or a message. In Chorus, we call such agents Passive Agents. Here is an example of defining a passive agent that reacts to human's message.

```python
class TestPassiveAgent(PassiveAgent):

    def respond(
        self, context: AgentContext, state: PassiveAgentState, inbound_message: Message
    ) -> Optional[PassiveAgentState]:
        if inbound_message.source == "human":
            context.message_service.send_message(Message(destination="human", content="Hello back.")
        return state
```

### ToolChat Agents

Chorus offers a set of pre-built agent classes for building LLM-based agents easily. One useful agent class is `ToolChatAgent`. It is a passive agent that can react to requester's message, orchestrate using tools and provide response back to the requester. Here is a code example of creating a ToolChatAgent using Claude model:

```python
from chorus.agents import ToolChatAgent
from chorus.toolbox.examples import WeatherTool

instruction = """
You are an agent helping to suggest a good trip location close to the location the user provided for this weekend. Please suggest the location based on weather, safety, experience and budget.
"""

agent = ToolChatAgent(
    name="Charlie",
    instruction=instruction,
    tools=[weather_tool],
    model_name="anthropic.claude-3-haiku-20240307-v1:0"
)
```

## Conclusion

In this page, we have discussed the key concepts related to agent design in Chorus, including the base agent contract, passive agents, and LLM-based agents with tool use. You can find more details on built-in agents in the docs. 