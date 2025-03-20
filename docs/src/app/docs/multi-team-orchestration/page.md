---
title: Multi-Team Orchestration
nextjs:
  metadata:
    title: Multi-Team Orchestration
    description: Building complex multi-agent workflows with Chorus for orchestrating multiple teams.
---

# Multi-Agent Workflow Programming

This example demonstrates how to create a multi-agent workflow for website development using Chorus. The workflow involves four specialized agents working together to create a website, with built-in quality assurance and refinement cycles.

## Agents Structure

The workflow consists of four specialized agents:

1. **Content Writer**: Creates engaging website content
   - Uses web search tools for research
   - Produces structured content with clear sections
   - Focuses on conversion-oriented copy

2. **Designer**: Creates design specifications
   - Defines color schemes with hex codes
   - Specifies typography and font families
   - Plans layout structure and component positioning
   - Establishes visual hierarchy
   - Provides spacing guidelines

3. **Developer**: Implements the website
   - Creates semantic HTML5 structure
   - Implements modern CSS3 with flexbox/grid
   - Ensures mobile-first approach
   - Refines implementation based on design specs

4. **QA Engineer**: Reviews implementation
   - Validates HTML/CSS
   - Checks responsive design
   - Verifies content accuracy
   - Ensures design compliance
   - Tests cross-browser compatibility

## Workflow Implementation

### Basic Setup

```python
from chorus.agents.tool_chat_agent import ConversationalTaskAgent
from chorus.core import Chorus
from chorus.toolbox import WebRetrieverTool, DuckDuckGoWebSearchTool
from chorus.helpers.communication import CommunicationHelper
from chorus.helpers.smart_logic import SmartLogicHelper

# Create agents
content_agent = ConversationalTaskAgent(
    "ContentWriter",
    instruction="You are a content writer specialized in creating engaging website content...",
    tools=[DuckDuckGoWebSearchTool(), WebRetrieverTool()]
)

designer_agent = ConversationalTaskAgent(
    "Designer",
    instruction="You are a web designer specialized in creating modern, responsive design specifications..."
)

developer_agent = ConversationalTaskAgent(
    "Developer",
    instruction="You are a web developer specialized in implementing websites using HTML5 and CSS3..."
)

qa_agent = ConversationalTaskAgent(
    "QAEngineer",
    instruction="You are a QA engineer specialized in reviewing website implementations..."
)

# Initialize Chorus
chorus = Chorus(agents=[content_agent, designer_agent, developer_agent, qa_agent])
```

### Run Chorus

Chorus can be run in a separate thread to avoid blocking the main execution:

```python
# Start Chorus (non-blocking)
chorus.start()

# Your workflow code here...

# Stop Chorus when done
chorus.stop()
```

Key considerations:
- `chorus.start()`: Non-blocking call that starts Chorus in a background thread
- `chorus.stop()`: Gracefully stops Chorus and its agents
- Always call `stop()` when finished to clean up resources
- Use `start()` for simpler workflows
- Use explicit thread management for more control over the Chorus lifecycle

### Parallel Processing Workflow

The workflow is designed to maximize efficiency through parallel processing. There are two ways to handle agent communication:

#### Using send_and_wait (Simplified Approach)

For simple sequential operations, you can use `send_and_wait` to combine sending a message and waiting for the response:

```python
# Content Creation Phase
content_response = comm.send_and_wait(
    destination="ContentWriter",
    content="Create content for landing page...",
    timeout=300  # Optional timeout in seconds
)
print("\nContent Created:", content_response.content)
```

#### Using separate send and wait (For Parallel Processing)

When you need more control or want to run tasks in parallel, use separate `send` and `wait` calls:

```python
# Send tasks simultaneously
comm.send(destination="Designer", content="Create design specs...")
comm.send(destination="Developer", content="Create initial implementation...")

# Wait for both responses
design_response = comm.wait(source="Designer")
dev_initial_response = comm.wait(source="Developer")
```

#### Communication Methods Comparison

1. **send_and_wait**
   - Pros:
     * More concise code
     * Built-in timeout handling
     * Simpler error handling
   - Best for:
     * Sequential operations
     * Single request-response patterns
     * When you don't need parallel processing

2. **separate send and wait**
   - Pros:
     * More control over the process
     * Enables parallel processing
     * Flexible response handling
   - Best for:
     * Parallel operations
     * Complex workflows
     * When you need to send multiple requests before waiting

Example of both approaches in the workflow:

```python
# Sequential operation using send_and_wait
content_response = comm.send_and_wait(
    destination="ContentWriter",
    content="Create content for landing page..."
)

# Parallel operations using separate send/wait
comm.send(destination="Designer", content=f"Create design specs:\n{content_response.content}")
comm.send(destination="Developer", content=f"Create initial implementation:\n{content_response.content}")

# Wait for parallel tasks
design_response = comm.wait(source="Designer")
dev_initial_response = comm.wait(source="Developer")

# Sequential refinement using send_and_wait
final_dev_response = comm.send_and_wait(
    destination="Developer",
    content=f"Refine implementation using design specs:\n{design_response.content}"
)
```

### Smart QA Loop

The workflow includes an intelligent QA process using `SmartLogicHelper`:

```python
while current_iteration < max_iterations:
    # Send for QA review
    comm.send(destination="QAEngineer", content="Review implementation...")
    qa_response = comm.wait(source="QAEngineer")

    # Use smart_judge to evaluate issues
    has_critical_issues = logic.smart_judge(
        qa_response.content,
        "Does the QA review indicate any critical issues?"
    )

    if not has_critical_issues:
        break

    # Send for refinement if needed
    comm.send(destination="Developer", content="Address QA issues...")
```

## Key Features

1. **Parallel Processing**: Design and initial development happen simultaneously
2. **Intelligent QA**: Uses smart_judge to evaluate quality issues
3. **Iterative Refinement**: Supports multiple rounds of improvements
4. **Quality Control**: Built-in QA feedback loop
5. **Structured Communication**: Clear message passing between agents

## Running the Example

Execute the example using:

```bash
python examples/python/multi_agent_workflow.py
```

The script will:
1. Create website content
2. Generate design specifications
3. Implement the website
4. Perform QA reviews
5. Refine implementation if needed

## Best Practices

1. **Clear Instructions**: Each agent has specific, focused responsibilities
2. **Structured Output**: Agents provide formatted responses for easy parsing
3. **Quality Gates**: QA feedback loop ensures quality standards
4. **Iteration Limits**: Maximum iteration count prevents infinite loops
5. **Smart Validation**: Uses smart_judge for objective quality assessment
