from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from chorus.agents.base import Agent
from chorus.data.context import AgentContext
from chorus.data.executable_tool import ExecutableTool
from chorus.data.dialog import Message
from chorus.data.dialog import Role
from chorus.executors import SimpleToolExecutor
from chorus.lms import LanguageModelClient
from chorus.agents import ToolChatAgent
from chorus.data.state import PassiveAgentState
from chorus.planners.base import MultiAgentPlanner
from chorus.prompters import InteractPrompter, BedrockConverseMultiAgentToolChatPrompter
from chorus.util.interact import extract_relevant_interaction_history, orchestrate
from chorus.toolbox.internal.agent_communication import MultiAgentTool
from chorus.config.globals import DEFAULT_AGENT_LLM_NAME
from jinja2 import Template

MULTI_AGENT_INSTRUCTION = """
This is a multi-agent environment. You can reach out to following agents:
<agents>{% for agent_name, agent_description in reachable_agents.items() %}
<agent name="{{agent_name}}">{{agent_description}}</agent>{% endfor %}
</agents>
""".strip()

@Agent.register("AsyncToolChatAgent")
class AsyncToolChatAgent(ToolChatAgent):
    """An asynchronous tool chat agent that can call other agents without blocking.

    This agent extends ToolChatAgent to enable asynchronous communication with other agents.
    It can execute tools and interact with other agents without waiting for responses,
    allowing for parallel processing and improved efficiency.

    Args:
        name: The name identifier for this agent.
        model_name: The name of the language model to use. Defaults to DEFAULT_AGENT_LLM_NAME.
        instruction: Custom instructions for the agent's behavior. Defaults to None.
        multi_agent_instruction: Additional instructions for multi-agent interactions. Defaults to None.
        tools: List of executable tools available to the agent. Defaults to None.
        prompter: Custom prompter for generating interactions. Defaults to None.
        lm: Language model client for text generation. Defaults to None.
        no_response_sources: List of sources to exclude from responses. Defaults to None.
        planner: Planner for solution strategies. Defaults to None.
        tool_executor_class: Class for executing tools. Defaults to SimpleToolExecutor.
        allow_waiting: Whether the agent can wait for tool completion. Defaults to False.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        model_name: str = DEFAULT_AGENT_LLM_NAME,
        instruction: Optional[str] = None,
        multi_agent_instruction: Optional[str] = None,
        reachable_agents: Optional[Dict[str, str]] = None,
        tools: Optional[List[ExecutableTool]] = None,
        prompter: Optional[InteractPrompter] = None,
        lm: Optional[LanguageModelClient] = None,
        no_response_sources: List[str] = None,
        planner: Optional[MultiAgentPlanner] = None,
        tool_executor_class: Type[SimpleToolExecutor] = SimpleToolExecutor,
        allow_waiting: bool = False,
    ):
        """Initializes the AsyncToolChatAgent.

        Args:
            name: Name of the agent.
            model_name: Name of the language model to use.
            instruction: Instruction for the agent.
            multi_agent_instruction: Additional instructions for multi-agent scenarios.
            tools: Tools for the agent.
            prompter: Prompter to use for generating interactions.
            lm: Language model client.
            no_response_sources: Sources that will not be included in the response.
            planner: Planner to use for planning solutions.
            tool_executor_class: Class to use for tool execution.
            allow_waiting: Whether to allow waiting for tools to finish.
        """
        self._allow_waiting = allow_waiting
        self._tool_executor_class = tool_executor_class
        if not instruction:
            agent_instruction = ""
        else:
            agent_instruction = instruction
        if multi_agent_instruction is None and reachable_agents is not None:
            multi_agent_instruction = Template(MULTI_AGENT_INSTRUCTION, autoescape=True).render(reachable_agents=reachable_agents) # from jinja2 import Template
        if multi_agent_instruction is not None:
            agent_instruction = f"{multi_agent_instruction}\n\n{agent_instruction}"
        agent_tools = [MultiAgentTool(allow_waiting=allow_waiting)]
        if tools is not None:
            agent_tools.extend(tools)
        super().__init__(
            name=name,
            model_name=model_name,
            instruction=agent_instruction,
            tools=agent_tools,
            prompter=prompter,
            lm=lm,
            no_response_sources=no_response_sources,
            planner=planner,
            tool_executor_class=tool_executor_class,
        )

    def infer_agent_prompter(self, model_name: str) -> Optional[InteractPrompter]:
        """Infers the appropriate prompter based on the model name.

        Args:
            model_name: Name of the language model.

        Returns:
            An appropriate InteractPrompter instance or None.

        Raises:
            NotImplementedError: If no prompter is implemented for the given model.
        """
        if model_name.startswith("anthropic.") or model_name.startswith("gpt-"):
            return BedrockConverseMultiAgentToolChatPrompter()
        else:
            raise NotImplementedError(f"Prompter for model {model_name} not implemented for AsynchronizedCoordinatorAgent agent.")
        return None

    def respond(
        self, context: AgentContext, state: Optional[PassiveAgentState], inbound_message: Message
    ) -> Optional[PassiveAgentState]:
        """Processes an inbound message and generates a response.

        Args:
            context: The context for the agent's operation.
            state: The current state of the agent.
            inbound_message: The message to respond to.

        Returns:
            The updated agent state after processing the message.
        """
        orchestrate(
            context=context,
            state=state,
            interaction_history=[],
            prompter=self._prompter,
            lm=self._lm,
            auto_tool_execution=True,
            planner=self._planner,
            dynamic_message_loading=True,
            multi_agent_tool_name=MultiAgentTool.TOOL_NAME,
            multi_agent_finish_action=MultiAgentTool.FINISH_ACTION_NAME,
            tool_executor_class=self._tool_executor_class,
        )
        return state
