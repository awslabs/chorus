# Chorus

A easy-to-use framework for building scalable solutions with LLM-driven multi-agent collaboration

Chorus allows you to develop and test solutions using multi-agent collaboration with zero or minimal coding. Chorus provides a multi-agent playground for easy visualization and testing.
Finally, Chorus helps you deploy your solution to Amazon Bedrock Agents with a single command (coming soon).


## Key Features

| **🤖  Scalable multi-agent inter-communication and collaboration support** <br><br> Chorus is designed by prioritizing scalability. The inter-communication mechanism allows easy scaling up to hundreds of agents and communicate with each other in real-time. | **🧬  Simple, yet customizable** <br><br> With Chorus, you can develop your solution using jsonnet descriptional language and zero coding. However, Chorus also provides utility for building customized agent logic with minimal Python coding. |
|---|---|
| **⚖  Build-in support for various tools, agents and multi-agent planners** <br><br> Chorus implements various useful tools, agents and dynamic planners for multi-agent collaboration. You can leverage them to create diverse agent teams for complex tasks such as developing a software. | **🖇️  Build upon examples and templates** <br><br> Chorus provides multiple examples with different collaboration patterns, allowing you easily boostrap for your own solution. |

**Current features and up-coming features:**

* Agent support
  * Chat-only agent, Tool-chat agent, Synchronized Meta Agent, Asynchroized Meta Agent
  * Action Agents and Agent Triggers
* Inter-communication
  * Message-based communication organized by channels,
  * Shared storage between agents 
* Multi-agent planners
  * Static plan (pre-defined plan), Dynamic goal planning
  * Asynchronized planning, Structured/Symbolic planning

## Installation

To get started, clone the repository and install the package.


```bash
git clone ssh://git.amazon.com/pkg/AWSChorus
cd AWSChorus
pip install -e .
```

Export AWS credentials to use models on Bedrock or SageMaker.

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
```

## Hello World Example

In the Chorus package, we provide a hello world example allows you to get started with Chorus quickly.



### Hello World Agent Team

In the hello world example, we built a simple agent team for answering questions related to fitness. The team consists of just three agents:

| Agent Name | Agent Type | Description |
| --- | --- | --- |
| FitnessAnsweringAgent | `SynchronizedCoordinatorAgent` | A coordinator agent that coordinates the other two agents to answer questions. |
| FactResearchAgent | `ToolChatAgent` | A fact research agent that can search the web for facts related to fitness. |
| KnowledgeAgent | `ToolChatAgent` | A knowledge agent that can answer general questions related to fitness. |


### Running the example

In general, there are two ways in Chorus for running a multi-agent solution: 1) Create a workspace and run it using Chorus CLI, 2) Write python code for your solution and run it directly.

#### Part 1: Run the workspace using Chorus CLI

Let first try to run a configured workspace using Chorus CLI. All the configurations and codes for the hello world example are already included in the Chorus package, so we can directly run it by executing the following command from the root folder of the Chorus package:

```bash
python -m chorus.cli --root examples/workspaces -w hello_world run
```

You should see the following prompt:
```bash
===========================================
(Press enter a messages, or press Enter / type 'exit' to quit.)
Human -> team:HelloWorldTeam: 
```

Try to ask a question such as `What are the best parks in New York City for running?`. You should be able to see that the `FactResearchAgent` was triggered by the coordinator (FitnessAnsweringAgent) and the final output should be something like the following:

```bash
===========================================
[DM] FitnessAnsweringAgent -> human:
Based on the research, here are the best parks for running in New York City, along with their key features:

1. Central Park - The crown jewel for NYC runners
- 6.1-mile main loop
- Popular 1.58-mile Reservoir Track
- Diverse terrain options
- Excellent amenities (water fountains, restrooms)
- Well-maintained and lit paths

2. Prospect Park (Brooklyn)
- 3.35-mile main loop
- Nice mix of hills and flat sections
- Less crowded alternative to Central Park
- Well-shaded paths perfect for summer running

...
```

In rare cases, you might get `RateLimitError` from the web search tool if you run the example too frequently. In such case, the agents will try to react to such incidents and give the best response without relying on the web search.

#### Part 2: Run the example using python code

The Chorus package includes a Python implementation of the exactly same agent team. You can run it by simply executing the following command:

```bash
python examples/python/hello_world.py
```

Once the script is executed, you should be able to see the same output as the one from the CLI example.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.