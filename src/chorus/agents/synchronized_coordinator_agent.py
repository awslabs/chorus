from typing import Dict
from typing import List
from typing import Optional

from chorus.agents.base import Agent
from chorus.agents.tool_chat_agent import ToolChatAgent
from chorus.data.executable_tool import ExecutableTool
from chorus.executors import SimpleToolExecutor
from chorus.lms import LanguageModelClient
from chorus.planners.base import MultiAgentPlanner
from chorus.prompters import InteractPrompter
from chorus.toolbox.internal.agent_communication import AgentAsATool
from chorus.config.globals import DEFAULT_AGENT_LLM_NAME
from typing import Type

@Agent.register("SynchronizedCoordinatorAgent")
class SynchronizedCoordinatorAgent(ToolChatAgent):
    """A coordinating agent that orchestrates the agents with synchronous communication.

    This agent acts as a coordinator between multiple sub-agents, routing messages and tasks
    to the appropriate agent based on the context and intent of each interaction.

    Args:
        name (str): Name of the agent.
        reachable_agents (Dict[str, str]): Dictionary mapping sub-agent names to their descriptions.
        model_name (str, optional): Name of the language model to use. Defaults to DEFAULT_AGENT_LLM_NAME.
        instruction (str, optional): Custom instruction for the agent. Defaults to None.
        tools (List[ExecutableTool], optional): List of additional executable tools. Defaults to None.
        prompter (InteractPrompter, optional): Prompter instance for generating interactions. Defaults to None.
        lm (LanguageModelClient, optional): Language model client instance. Defaults to None.
        no_response_sources (List[str], optional): List of sources to ignore responses from. Defaults to None.
        planner (MultiAgentPlanner, optional): Planner instance for solution planning. Defaults to None.
        tool_executor_class (Type[SimpleToolExecutor], optional): Class for tool execution. Defaults to SimpleToolExecutor.
    """

    def __init__(
        self,
        name: str,
        reachable_agents: Dict[str, str],
        model_name: str = DEFAULT_AGENT_LLM_NAME,
        instruction: Optional[str] = None,
        tools: List[ExecutableTool] = None,
        prompter: Optional[InteractPrompter] = None,
        lm: Optional[LanguageModelClient] = None,
        no_response_sources: Optional[List[str]] = None,
        planner: Optional[MultiAgentPlanner] = None,
        tool_executor_class: Type[SimpleToolExecutor] = SimpleToolExecutor,
    ):
        """Initialize the SynchronizedCoordinatorAgent.

        Args:
            name: Name of the agent.
            reachable_agents: Dictionary of sub-agent names and their corresponding descriptions.
            model_name: Name of the language model to use.
            instruction: Custom instruction for the agent.
            tools: List of additional executable tools.
            prompter: Prompter to use for generating interactions.
            lm: Language model client.
            no_response_sources: List of sources to ignore responses from.
            planner: Planner to use for planning solutions.
            tool_executor_class: Class for tool execution.
        """
        no_response_sources = list(reachable_agents.keys()) + (no_response_sources or [])
        agent_tools = [
            AgentAsATool(sub_agent_name, sub_agent_desc)
            for sub_agent_name, sub_agent_desc in reachable_agents.items()
        ]
        if tools:
            agent_tools.extend(tools)
        super().__init__(
            name=name,
            model_name=model_name,
            instruction=instruction,
            tools=agent_tools,
            prompter=prompter,
            lm=lm,
            no_response_sources=no_response_sources,
            planner=planner,
            tool_executor_class=tool_executor_class,
        )