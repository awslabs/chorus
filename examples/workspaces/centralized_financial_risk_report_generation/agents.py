import time
from chorus.agents import Agent, SynchronizedCoordinatorAgent
from chorus.helpers import CommunicationHelper
from chorus.data import Message, AgentContext
from chorus.data.state import PassiveAgentState

@Agent.register("FinancialAnalysisCoordinatorAgent")
class FinancialAnalysisCoordinatorAgent(SynchronizedCoordinatorAgent):

    def respond(self, context: AgentContext, state: PassiveAgentState, inbound_message: Message) -> PassiveAgentState:
        comm = CommunicationHelper(context)
        if inbound_message.source != "human":
            return state
        # Analyzing the company with regular workflow
        first_message = Message(
            destination=context.agent_id,
            source="Supervisor",
            content=inbound_message.content,
        )
        context.message_service.send_message(first_message)
        super().respond(context, state, first_message)
        all_messages = context.message_service.fetch_all_messages()
        all_messages[-1].source=context.agent_id
        context.message_service.refresh_history(all_messages)
        second_message = Message(
            destination=context.agent_id,
            source="Supervisor",
            content="Discuss with sub agents for 3 rounds in order to clarify and align the opinions."
        )
        context.message_service.send_message(second_message)
        time.sleep(10)
        super().respond(context, state, second_message)
        all_messages = context.message_service.fetch_all_messages()
        all_messages[-1].source = context.agent_id
        context.message_service.refresh_history(all_messages)

        # Final message is coming from supervisor
        comm.send(
            destination="human",
            content=all_messages[-1].content
        )
        return state
