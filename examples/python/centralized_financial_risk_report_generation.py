import time
from chorus.agents import TaskCoordinatorAgent, ConversationalTaskAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.core.runner import Chorus
from chorus.data import Message, AgentContext
from chorus.data.state import PassiveAgentState
from chorus.helpers import CommunicationHelper

from chorus.toolbox import SerperWebSearchTool, WebRetrieverToolV2, RemotePDFReaderTool
from chorus.workspace.stop_conditions import NoActivityStopper

class FinancialAnalysisCoordinatorAgent(TaskCoordinatorAgent):

    def respond(self, context: AgentContext, state: PassiveAgentState, inbound_message: Message) -> PassiveAgentState:
        comm = CommunicationHelper(context)
        if inbound_message.source != "human":
            return state

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

        comm.send(
            destination="human",
            content=all_messages[-1].content
        )
        return state
    

if __name__ == '__main__':
    reachable_agents = {
        "FinancialStatementRetriever": "This is an agent helps to retrieve financial statements of the company",
        "SentimentRiskAnalyzerAgent": "This is an agent analyzes the sentiment of the company's news and social media posts",
        "ManagementRiskAnalyzerAgent": "This is an agent analyzes the management team's recent change, performance, and reputation",
        "FinancialHealthAnalyzerAgent": "This is an agent helping to analyze the company's financial health risk such as long-term liquidity, debt, and cash flow",
        "GlobalEconomyAnalyzerAgent": "This is an agent helping to analyze company's risk exposure to the global economy such as GDP, inflation, and interest rates",
    }

    coordinator = FinancialAnalysisCoordinatorAgent(
        "RiskAnalysisCoordinator",
        instruction="""
        Given a company name or its stock symbol, coordinate with several agents to generate a comprehensive risk analysis report.
        Notes:
        - Call FinancialStatementRetriever to retrieve the company's financial statements first.
        - When you talk to a sub agent, include the financial result when you think it is relevant.
        - For each section, provide as much details as possible.
        - In your final response back to human, generate a comprehensive report as your final response with simple HTML, follow this format:
            <report>
            <h2>Risk Analysis Report for Company XYZ</h2>

            <h3>Summary</h3>
            <p> ... </p>

            <h3>Financial Health Risks</h3>
            <p> ... </p>

            <h3>Global Economic Risks</h3>
            <p> ... </p>

            <h3>Management Risks</h3>
            <p> ... </p>

            <h3>Sentiment Risks</h3>
            <p> ... </p>

            <h3>References</h3>
            <p><ul>
              <li><a href="...">...</a></li>
              ...
            </ul></p>
            </report>
        - You can insert charts into the report using <img/> tag.
        """,
        reachable_agents=reachable_agents,
        model_name="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )

    sentiment_analyzer = ConversationalTaskAgent(
        "SentimentRiskAnalyzerAgent",
        instruction="""
        You are a sentiment risk analyzer.
        Search for news, articles and social media posts related to the company and analyze the sentiment of them.
        Provide a summary of analysis results and findings.

        Notes:
        - You can include URLs of useful charts, images and relevant articles in your response.
        """,
        tools=[SerperWebSearchTool(), WebRetrieverToolV2()],
        model_name="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )

    management_analyzer = ConversationalTaskAgent(
        "ManagementRiskAnalyzerAgent", 
        instruction="""
        You are a management risk analyzer.
        Gather information from the management team such as recent changes, performance, and reputation.
        Provide a summary of analysis results and findings.

        Notes:
        - You can include URLs of useful charts, images and relevant articles in your response.
        """,
        tools=[SerperWebSearchTool(), WebRetrieverToolV2()],
        model_name="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )

    financial_analyzer = ConversationalTaskAgent(
        "FinancialHealthAnalyzerAgent",
        instruction="""
        You are a financial health analyzer.
        Gather information from the company's financial statements such as long-term liquidity, debt, and cash flow.
        Analyze the risk of the company's financial health.
        Provide a summary of analysis results and findings.

        Notes:
        - You can include URLs of useful charts, images and relevant articles in your response.
        """,
        tools=[SerperWebSearchTool(), WebRetrieverToolV2()],
        model_name="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )

    economy_analyzer = ConversationalTaskAgent(
        "GlobalEconomyAnalyzerAgent",
        instruction="""
        You are a global economy analyzer.
        Gather information from the global economy such as GDP, inflation, and interest rates.
        Analyze the risk exposure of the company to these factors.
        Provide a summary of analysis results and findings.

        Notes:
        - You can include URLs of useful charts, images and relevant articles in your response.
        """,
        tools=[SerperWebSearchTool(), WebRetrieverToolV2()],
        model_name="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )

    statement_retriever = ConversationalTaskAgent(
        "FinancialStatementRetriever",
        instruction="""
        You are a financial statement retriever.
        Your job is to search and retrieve the company financial statements. You can read remote PDF file and return the content.
        Generate a comprehensive report of the financial statements including as much details as possible in your final response.
        """,
        tools=[SerperWebSearchTool(), WebRetrieverToolV2(), RemotePDFReaderTool()],
        model_name="anthropic.claude-3-5-sonnet-20240620-v1:0"
    )

    team = Team(
        name="FinancialRiskAnalysisTeam",
        agents=[
            coordinator,
            sentiment_analyzer,
            management_analyzer,
            financial_analyzer,
            economy_analyzer,
            statement_retriever
        ],
        collaboration=CentralizedCollaboration(
            coordinator=coordinator.get_name()
        )
    )

    chorus = Chorus(
        teams=[team],
        stop_conditions=[NoActivityStopper()],
        visual=True,
        visual_port=5000
    )

    chorus.get_environment().send_message(
        source="human",
        destination=team.get_identifier(),
        content="SBUX, quarter report can be found at https://s203.q4cdn.com/326826266/files/doc_financials/2024/q3/3Q24-Earnings-Release-Final-7-30-24.pdf"
    )
    chorus.run()