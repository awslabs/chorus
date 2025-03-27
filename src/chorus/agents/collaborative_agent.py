from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from pydantic import Field

from chorus.agents.base import Agent
from chorus.data.context import AgentContext
from chorus.data.executable_tool import ExecutableTool
from chorus.data.dialog import Message
from chorus.data.dialog import EventType
from chorus.executors import SimpleToolExecutor
from chorus.lms import LanguageModelClient
from chorus.agents import ConversationalTaskAgent
from chorus.data.state import PassiveAgentState
from chorus.planners.base import MultiAgentPlanner
from chorus.communication.message_view_selectors import ChannelMessageViewSelector, MessageViewSelector
from chorus.prompters import InteractPrompter, BedrockConverseMultiAgentToolChatPrompter
from chorus.util.communication import select_message_view
from chorus.util.interact import orchestrate_generate_next_actions, orchestrate_execute_actions
from chorus.toolbox.internal.collaborative_agent_tools import AgentCommunicationTool
from chorus.toolbox.internal.agent_control_tool import AgentControlTool
from chorus.config.globals import DEFAULT_AGENT_LLM_NAME
from jinja2 import Template

MULTI_AGENT_INSTRUCTION = """
This is a multi-agent environment. You can reach out to following agents:
<agents>{% for agent_name, agent_description in reachable_agents.items() %}
<agent name="{{agent_name}}">{{agent_description}}</agent>{% endfor %}
</agents>
""".strip()

class CollaborativeAgentContext(AgentContext):
    """Context for a collaborative agent.

    Args:
        reachable_agents: Optional map of agents who can be reached out to
    """
    reachable_agents: Optional[Dict[str, str]] = Field(default_factory=dict[str, str])

    
@Agent.register("CollaborativeAgent")
class CollaborativeAgent(ConversationalTaskAgent):
    """An asynchronous tool chat agent that can call other agents without blocking.

    This agent extends ConversationalTaskAgent to enable asynchronous communication with other agents.
    It can execute tools and interact with other agents without waiting for responses,
    allowing for parallel processing and improved efficiency.

    Args:
        name: The name identifier for this agent.
        model_name: The name of the language model to use. Defaults to DEFAULT_AGENT_LLM_NAME.
        instruction: Custom instructions for the agent's behavior. Defaults to None.
        multi_agent_instruction: Additional instructions for multi-agent interactions. Defaults to None.
        reachable_agents: Optional map of agents who can be reached out to. Defaults to None.
        tools: List of executable tools available to the agent. Defaults to None.
        communication_tool: 
        prompter: Custom prompter for generating interactions. Defaults to None.
        lm: Language model client for text generation. Defaults to None.
        no_response_sources: List of sources to exclude from responses. Defaults to None.
        planner: Planner for solution strategies. Defaults to None.
        message_view_selector: a message selector/filter that decides which messages this agent should see. Defaults to None.
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
        communication_tool: Optional[ExecutableTool] = None,
        control_tool: Optional[AgentControlTool] = None,
        prompter: Optional[InteractPrompter] = None,
        lm: Optional[LanguageModelClient] = None,
        no_response_sources: Optional[List[str]] = None,
        planner: Optional[MultiAgentPlanner] = None,
        message_view_selector: Optional[MessageViewSelector] = None,
        tool_executor_class: Type[SimpleToolExecutor] = SimpleToolExecutor,
        allow_waiting: bool = False,
    ):
        """Initializes the CollaborativeAgent.

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
            message_view_selector: Message view selector to use for selecting messages.
            tool_executor_class: Class to use for tool execution.
            allow_waiting: Whether to allow waiting for tools to finish.
        """
        self._allow_waiting = allow_waiting
        self.reachable_agents = reachable_agents
        if not instruction:
            agent_instruction = ""
        else:
            agent_instruction = instruction
        if multi_agent_instruction is None and reachable_agents is not None:
            multi_agent_instruction = Template(MULTI_AGENT_INSTRUCTION, autoescape=True).render(reachable_agents=reachable_agents) # from jinja2 import Template
        if multi_agent_instruction is not None:
            agent_instruction = f"{multi_agent_instruction}\n\n{agent_instruction}"
        
        self._communication_tool = communication_tool
        if self._communication_tool is None:
            self._communication_tool = AgentCommunicationTool(allow_waiting=allow_waiting)
        self._control_tool = control_tool
        if self._control_tool is None:
            self._control_tool = AgentControlTool()
        self._agent_control_tool_name = self._control_tool.get_schema().tool_name
        self._agent_control_finish_action_name = self._control_tool.get_finish_action_name()

        # Setup tools
        agent_tools = [self._communication_tool, self._control_tool]
        if tools is not None:
            agent_tools.extend(tools)
        
        # Setup message view selector
        if message_view_selector is not None:
            self._message_view_selector = message_view_selector
        else:
            self._message_view_selector = ChannelMessageViewSelector(include_internal_events=True)
    
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
    
    def init_context(self) -> CollaborativeAgentContext:
        """Initialize the context for the collaborative agent.
        """
        context = CollaborativeAgentContext(
            agent_id=self.create_agent_context_id(),
            message_view_selector=self._message_view_selector,
            reachable_agents=self.reachable_agents,
            agent_instruction=self._instruction
        )
        if self._tools:
            context.tools = self._tools
        return context

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
            raise NotImplementedError(f"Prompter for model {model_name} not implemented for ATaskCoordinatorAgent agent.")
        return None

    def respond(
        self, context: AgentContext, state: PassiveAgentState, inbound_message: Message
    ) -> PassiveAgentState:
        """Processes an inbound message and generates a response.

        Args:
            context: The context for the agent's operation.
            state: The current state of the agent.
            inbound_message: The message to respond to.

        Returns:
            The updated agent state after processing the message.
        """
        # Initialize tool executor
        executor = self._tool_executor_class(context.get_tools(), context)
        
        # Fetch all messages for this agent, merge with internal events
        external_messages = context.message_service.fetch_all_messages()
        message_view = select_message_view(context, state, external_messages)
        history = message_view.messages

        # Generate next actions
        output_messages = orchestrate_generate_next_actions(
            context=context,
            state=state,
            interaction_history=history,
            prompter=self._prompter,
            lm=self._lm,
            planner=self._planner,
        )
        
        while output_messages and output_messages[-1].actions:
            action_message = output_messages[-1]
            # Check if the last action is a finish action
            finish_action_generated = False
            if action_message.actions is not None:
                for action in action_message.actions:
                    if action.tool_name == self._agent_control_tool_name and action.action_name == self._agent_control_finish_action_name:
                        finish_action_generated = True
                        break
            if finish_action_generated:
                break

            # Execute the actions
            observation_message = orchestrate_execute_actions(
                context=context,
                action_message=action_message,
                executor=executor,
            )

            # Record internal events since external outbound messages are already sent out
            action_recorded = False
            last_message_actions = output_messages[-1].actions[:]
            for message in output_messages:
                # Skip if the message doesn't have an action
                if message.event_type != EventType.INTERNAL_EVENT:
                    continue
                # Modify the message to remove communication actions
                if message.actions:
                    if self._communication_tool is not None:
                        message.actions = [action for action in message.actions if action.tool_name != self._communication_tool.get_schema().tool_name]
                    action_recorded = True
                state.internal_events.append(message)
            
            # If non-communication actions are recorded, then also record the corresponding observations
            if action_recorded and observation_message is not None:
                observations = observation_message.observations
                non_communication_observations = []
                assert len(observations) == len(last_message_actions)
                for observation, action in zip(observations, last_message_actions):
                    if self._communication_tool is not None and action.tool_name != self._communication_tool.get_schema().tool_name:
                        non_communication_observations.append(observation)
                observation_message.observations = non_communication_observations
                state.internal_events.append(observation_message)
     
            # Generate follow-up responses by retrieving fresh messages and selecting a message view
            external_messages = context.message_service.fetch_all_messages()
            message_view = select_message_view(context, state, external_messages)
            history = message_view.messages
            output_messages = orchestrate_generate_next_actions(
                context=context,
                state=state,
                interaction_history=history,
                prompter=self._prompter,
                lm=self._lm,
                planner=self._planner,
            )
            
        
        return state
