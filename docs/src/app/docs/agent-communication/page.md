---
title: Agent Communication
description: Learn about communication between agents in Chorus
---

# Agent Communication

## Messages

In Chorus, agents have multiple ways to share knowledge and information. The most common way for agents to communicate is through message passing. In Chorus, a message is considered as a special type of event that is sent between agents. A message object has the following properties:

- `source`: the agent that sends the message.
- `destination`: the agent that receives the message.
- `content`: the content of the message.
- `channel`: the communication channel used to send the message. If the channel is not specified, the message will be a direct message between the source and destination agents.
- `metadata`: additional information about the message.

## Communication Channels

### Overview

Communication channels in Chorus provide a mechanism for group communication between agents. They act as virtual spaces where multiple agents can share information, coordinate activities, and maintain group awareness without needing to send individual messages to each member.

### Understanding Communication Channels

A channel in Chorus is defined by:
1. A unique name identifier
2. A list of member agents who can participate
3. Optional channel-specific configurations

### Basic Channel Usage

Here's a simple example of setting up a communication channel:

```python
from chorus.data.channel import Channel
from chorus.agents import ConversationalTaskAgent
from chorus.core import Chorus

# Create a channel
news_channel = Channel(
    name="news_channel",
    members=["NewsAnchor", "NewsReporter", "WeatherReporter"]
)

# Create agents
news_anchor = ConversationalTaskAgent(
    name="NewsAnchor",
    instruction="Monitor news_channel and coordinate news broadcasts"
)

news_reporter = ConversationalTaskAgent(
    name="NewsReporter",
    instruction="Report news on news_channel"
)

# Initialize Chorus with the channel
chorus = Chorus(
    agents=[news_anchor, news_reporter],
    channels=[news_channel]
)
```

### How Channels Work

#### Message Distribution

When an agent sends a message to a channel:
1. The message is automatically distributed to all channel members
2. Each member receives a copy of the message with the channel field set
3. Messages include the original sender's information
4. All channel members can observe the conversation

Example of sending a channel message:
```python
from chorus.data.dialog import Message, Role

# Send a message to the channel
message = Message(
    source="NewsReporter",
    channel="news_channel",  # Specify the channel instead of destination
    content="Breaking news: New technology breakthrough!",
    role=Role.USER
)
```

### Channel Best Practices

1. **Purpose-Specific Channels**: Create channels with clear purposes to avoid confusion
   ```python
   tech_channel = Channel(
       name="tech_news",
       members=["TechReporter", "TechAnalyst"]
   )
   weather_channel = Channel(
       name="weather_updates",
       members=["WeatherReporter", "EmergencyCoordinator"]
   )
   ```

2. **Member Management**: Keep member lists focused and relevant
   ```python
   # Good: Clear purpose and relevant members
   emergency_channel = Channel(
       name="emergency_alerts",
       members=["EmergencyCoordinator", "FirstResponder", "WeatherReporter"]
   )
   ```

3. **Channel Instructions**: Include channel information in agent instructions
   ```python
   agent = ConversationalTaskAgent(
       name="NewsReporter",
       instruction="""
       Here are the channels available for communication:
       <channels>
       <channel name="breaking_news" description="Urgent news updates"/>
       <channel name="daily_news" description="Regular news reporting"/>
       </channels>
       
       Your role:
       - Report breaking news in breaking_news channel
       - Share regular updates in daily_news channel
       """
   )
   ```

## Direct Communication

In addition to channel-based communication, agents can communicate directly with each other:

```python
# Send a direct message
chorus.get_environment().send_message(
    source="Researcher",
    destination="Analyst",
    content="Here's the data you requested for analysis."
)
```

Direct communication is useful for one-on-one interactions between agents, while channels are better for group communication. 