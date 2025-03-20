from typing import List, Tuple
from typing import Optional
from typing import Type

from chorus.agents import Agent
from chorus.communication.message_view_selectors import DirectMessageViewSelector
from chorus.data.context import AgentContext, OrchestrationContext
from chorus.data.executable_tool import ExecutableTool
from chorus.data.dialog import Message
from chorus.data.dialog import EventType
from chorus.data.trigger import BaseTrigger, MessageTrigger
from chorus.executors import SimpleToolExecutor
from chorus.lms import LanguageModelClient
from chorus.agents.passive_agent import PassiveAgent
from chorus.data.state import PassiveAgentState
from chorus.lms.bedrock_converse import BedrockConverseAPIClient
from chorus.planners.base import MultiAgentPlanner
from chorus.prompters import InteractPrompter
from chorus.prompters.interact.bedrock_converse_tool_chat import BedrockConverseToolChatPrompter
from chorus.util.communication import select_message_view
from chorus.util.interact import orchestrate_generate_next_actions, orchestrate_execute_actions
from chorus.config.globals import DEFAULT_AGENT_LLM_NAME

@Agent.register("ConversationalTaskAgent")
class ConversationalTaskAgent(PassiveAgent):
    """A chat agent that can use tools to assist with tasks.

    This agent extends PassiveAgent to enable tool usage and chat interactions. It can
    execute tools, process messages, and maintain conversations while leveraging various
    language models and prompters.

    Args:
        name: The name for this agent.
        model_name: The name of the language model to use. Defaults to DEFAULT_AGENT_LLM_NAME.
        instruction: Custom instructions for the agent's behavior. Defaults to None.
        tools: List of executable tools available to the agent. Defaults to None.
        prompter: Custom prompter for generating interactions. Defaults to None.
        lm: Language model client for text generation. Defaults to None.
        no_response_sources: List of sources to exclude from responses. Defaults to None.
        planner: Planner for solution strategies. Defaults to None.
        tool_executor_class: Class for executing tools. Defaults to SimpleToolExecutor.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        model_name: str = DEFAULT_AGENT_LLM_NAME,
        instruction: Optional[str] = None,
        tools: Optional[List[ExecutableTool]] = None,
        prompter: Optional[InteractPrompter] = None,
        lm: Optional[LanguageModelClient] = None,
        no_response_sources: Optional[List[str]] = None,
        planner: Optional[MultiAgentPlanner] = None,
        tool_executor_class: Type[SimpleToolExecutor] = SimpleToolExecutor,
        context_switchers: Optional[List[Tuple[MessageTrigger, OrchestrationContext]]] = None,
    ):
        super().__init__(name=name, no_response_sources=no_response_sources)
        self._prompter = prompter
        self._planner = planner
        self._tool_executor_class = tool_executor_class
        self._lm = lm
        self._tools = tools
        self._model_name = model_name
        self._instruction = instruction
        self._context_switchers = context_switchers if context_switchers else []
        # Infer language model and prompter if not provided
        if not self._lm:
            self._lm = self.infer_agent_lm(self._model_name)
            if not self._lm:
                raise ValueError(f"Language model client cannot be inferred using model name {self._model_name}. Please specify a valid language model client.")
        if not self._prompter:
            self._prompter = self.infer_agent_prompter(self._model_name)
            if not self._prompter:
                raise ValueError(f"Agent prompter cannot be inferred using model name {self._model_name}. Please specify a valid agent prompter.")

    def init_context(self) -> AgentContext:
        """Initialize the agent's context with tools and instructions.

        Returns:
            AgentContext: A new context object containing the agent's configuration.
        """
        context = AgentContext(
            agent_id=self.create_agent_context_id(),
            agent_instruction=self._instruction,
            message_view_selector=DirectMessageViewSelector(include_internal_events=True),
        )
        if self._tools:
            context.tools = self._tools
        return context

    def infer_agent_lm(self, model_name: str) -> Optional[LanguageModelClient]:
        """Infer a language model client based on the agent model name.

        Args:
            model_name: The name of the model to infer a client for.

        Returns:
            Optional[LanguageModelClient]: A language model client if one can be inferred,
                None otherwise.
        """
        lm_client = None
        if model_name.startswith("anthropic."):
            lm_client = BedrockConverseAPIClient(model_name)
            lm_client.set_default_options(
                {
                    "maxTokens": 2048,
                }
            )
            if model_name.startswith("anthropic.claude-2"):
                raise NotImplementedError(
                    "Claude 2 models are no longer supported. Please use newer versions of Claude models."
                )
        return lm_client

    def infer_agent_prompter(self, model_name: str) -> Optional[InteractPrompter]:
        """Infer an interact prompter based on the agent model name.

        Args:
            model_name: The name of the model to infer a prompter for.

        Returns:
            Optional[InteractPrompter]: A prompter if one can be inferred, None otherwise.
        """
        prompter = None
        if model_name.startswith("anthropic."):
            prompter = BedrockConverseToolChatPrompter()
        return prompter

    def get_prompter(self):
        """Get the agent's prompter instance.

        Returns:
            InteractPrompter: The prompter used by this agent.
        """
        return self._prompter

    def get_planner(self):
        """Get the agent's planner instance.

        Returns:
            MultiAgentPlanner: The planner used by this agent.
        """
        return self._planner

    def get_lm(self):
        """Get the agent's language model client.

        Returns:
            LanguageModelClient: The language model client used by this agent.
        """
        return self._lm

    def get_name(self):
        """Get the agent's name.

        Returns:
            str: The name of this agent.
        """
        return self._name

    def get_instruction(self):
        """Get the agent's instruction.

        Returns:
            Optional[str]: The instruction string for this agent.
        """
        return self._instruction

    def get_tools(self):
        """Get the agent's available tools.

        Returns:
            List[ExecutableTool]: List of tools available to this agent.
        """
        return self._tools
    
    def respond(
        self, context: AgentContext, state: PassiveAgentState, inbound_message: Message
    ) -> PassiveAgentState:
        """Process and respond to an incoming message.

        Handles message processing, tool execution, and async observations. Generates
        appropriate responses using the configured language model and prompter.

        Args:
            context: The agent's context containing environmental information.
            state: The current state of the agent.
            inbound_message: The message to respond to.

        Returns:
            PassiveAgentState: The updated agent state after processing.
        """
        # Check for context switches and switch if necessary
        for trigger, orch_context in reversed(self._context_switchers):
            if trigger.matches(inbound_message):
                # Update context with new orchestration context
                for field_name, field_value in orch_context.model_dump().items():
                    setattr(context, field_name, field_value)
                break
        
        # Create a message view
        all_messages = context.message_service.fetch_all_messages()
        message_view = select_message_view(context, state, all_messages)
        history = message_view.messages
        
        inbound_source = inbound_message.source
        # Process async observations
        if inbound_message.observations:
            async_observation_detected = False
            async_messages = []
            for observation in inbound_message.observations:
                if observation.async_execution_id is not None:
                    async_cache = context.get_async_execution_cache()
                    if observation.async_execution_id in async_cache:
                        async_record = async_cache[observation.async_execution_id]
                        observation.tool_use_id = async_record.tool_use_id
                        async_observe_message = Message(
                            source=context.agent_id,
                            destination=async_record.action_source,
                            channel=async_record.action_channel,
                            observations=[observation],
                            event_type=EventType.INTERNAL_EVENT
                        )
                        async_messages.append(async_observe_message)
                        async_observation_detected = True
                        inbound_source = async_record.action_source
            if async_observation_detected and async_messages:
                context.message_service.send_messages(async_messages)
                # Refresh the message view after sending new messages
                all_messages = context.message_service.fetch_all_messages()
                new_inbound = Message(source=inbound_source, destination=context.agent_id)
                message_view = context.message_view_selector.select(all_messages, new_inbound)
                history = message_view.messages

        # Initialize tool executor
        executor = self._tool_executor_class(context.get_tools(), context)
        
        # Generate next actions
        output_turns = orchestrate_generate_next_actions(
            context=context,
            state=state,
            interaction_history=history,
            prompter=self._prompter,
            lm=self._lm,
            planner=self._planner,
        )

        while output_turns and output_turns[-1].actions:
            # Execute the actions
            observation_message = orchestrate_execute_actions(
                context=context,
                action_message=output_turns[-1],
                executor=executor,
            )
            if observation_message is not None:
                output_turns.append(observation_message)
            
            # Generate follow-up responses
            follow_up_turns = orchestrate_generate_next_actions(
                context=context,
                state=state,
                interaction_history=history + output_turns,
                prompter=self._prompter,
                lm=self._lm,
                planner=self._planner,
            )
            
            # Add the follow-up turns to the output
            output_turns.extend(follow_up_turns)
        
        # Save internal events from output_turns into the state's internal_events
        external_events = []
        for turn in output_turns:
            if turn.event_type == EventType.INTERNAL_EVENT:
                turn.source = context.agent_id
                turn.destination = context.agent_id
                state.internal_events.append(turn)
            else:
                turn.destination = inbound_source
                turn.source = context.agent_id
                external_events.append(turn)
        context.message_service.send_messages(external_events)
        return state

    def on(self, trigger: BaseTrigger, orch_context: OrchestrationContext) -> 'ConversationalTaskAgent':
        """Add a context switcher for this agent.

        Args:
            trigger: The trigger to listen for.
            orch_context: The context to switch to when the trigger is detected.
        """
        self._context_switchers.append((trigger, orch_context))
        return self
    
    def remove_trigger(self, trigger: BaseTrigger, orch_context: OrchestrationContext):
        """Remove a context switcher for this agent.

        Args:
            trigger: The trigger to remove.
            orch_context: The context to remove.
        """
        self._context_switchers.remove((trigger, orch_context))
    
    def get_triggers(self) -> List[BaseTrigger]:
        """Get the triggers for this agent.

        Returns:
            List[BaseTrigger]: The triggers for this agent.
        """
        return [trigger for trigger, _ in self._context_switchers]
