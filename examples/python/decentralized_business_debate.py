from chorus.agents import AsyncToolChatAgent
from chorus.teams import Team
from chorus.collaboration import DecentralizedCollaboration
from chorus.core.runner import Chorus
from chorus.teams.services.team_voting import TeamVoting
from chorus.teams.toolbox.team_voting import TeamVotingClient
from chorus.data.collaboration_strategies import DecisionMakingStrategy
from chorus.workspace.stop_conditions import NoActivityStopper
from chorus.data.channel import Channel
from chorus.workspace.stop_conditions.message_based import MessageBasedStopper

if __name__ == '__main__':
    # Create a team channel for business debate
    debate_channel = Channel(
        name="business_debate",
        description="Channel for team members to discuss and analyze business proposals"
    )

    # Create agents with different business expertise
    financial_analyst = AsyncToolChatAgent(
        "FinancialAnalyst",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="business_debate" description="Channel for team members to discuss and analyze business proposals"/>
        </channels>

        You are a financial analyst who evaluates business proposals from a financial perspective.
        
        When you propose, the proposal content has to be either "feasible" or "not feasible" with a reasoning.

        When analyzing a business proposal:
        1. Share your initial financial analysis in the business_debate channel
        2. Focus on ROI, cash flow projections, and financial risks
        3. Evaluate market size and revenue potential
        4. Consider funding requirements and potential funding sources
        5. Propose your recommendation with clear financial reasoning
        6. Vote based on financial viability
        Keep messages concise and focused on financial aspects.
        Actively participate in discussions about financial implications.""",
        tools=[TeamVotingClient()]
    )

    market_strategist = AsyncToolChatAgent(
        "MarketStrategist",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="business_debate" description="Channel for team members to discuss and analyze business proposals"/>
        </channels>

        You are a market strategist who evaluates business proposals from a market perspective.

        When you propose, the proposal content has to be either "feasible" or "not feasible" with a reasoning.

        When analyzing a business proposal:
        1. Share your market analysis in the business_debate channel
        2. Focus on market trends, competition, and target audience
        3. Evaluate market entry barriers and opportunities
        4. Consider brand positioning and marketing strategy
        5. Propose your recommendation with clear market reasoning
        6. Vote based on market viability
        Keep messages concise and focused on market aspects.
        Actively participate in discussions about market dynamics.""",
        tools=[TeamVotingClient()]
    )

    operations_expert = AsyncToolChatAgent(
        "OperationsExpert",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="business_debate" description="Channel for team members to discuss and analyze business proposals"/>
        </channels>

        You are an operations expert who evaluates business proposals from an operational perspective.

        When you propose, the proposal content has to be either "feasible" or "not feasible" with a reasoning.

        When analyzing a business proposal:
        1. Share your operational analysis in the business_debate channel
        2. Focus on scalability, resource requirements, and operational risks
        3. Evaluate supply chain and logistics feasibility
        4. Consider technical requirements and implementation challenges
        5. Propose your recommendation with clear operational reasoning
        6. Vote based on operational viability
        Keep messages concise and focused on operational aspects.
        Actively participate in discussions about implementation challenges.""",
        tools=[TeamVotingClient()]
    )

    # Create team with voting service and decentralized collaboration
    business_team = Team(
        name="BusinessEvaluationTeam",
        agents=[financial_analyst, market_strategist, operations_expert],
        services=[
            TeamVoting(
                decision_making_strategy=DecisionMakingStrategy.MAJORITY_VOTE,
                proposal_duration_seconds=300  # 5 minutes for debate and voting
            )
        ],
        collaboration=DecentralizedCollaboration(
            time_limit=300  # 5 minutes total time limit
        )
    )

    # Create chorus runner with debate channel
    chorus = Chorus(
        teams=[business_team],
        channels=[debate_channel],
        stop_conditions=[MessageBasedStopper(source=business_team.get_identifier(), destination="human")],
        visual=True,
        visual_port=5000
    )

    # Send a business proposal for evaluation
    chorus.get_environment().send_message(
        source="human",
        destination=business_team.get_identifier(),
        content="""
        Please evaluate the following business proposal:

        Business Concept: AI-Powered Personal Shopping Assistant
        
        Product Description:
        - Mobile app that uses AI to provide personalized shopping recommendations
        - Learns user preferences from browsing history and purchase patterns
        - Integrates with major e-commerce platforms
        - Offers price comparison and deal alerts
        
        Target Market:
        - Primary: Tech-savvy online shoppers (25-45 years)
        - Secondary: Busy professionals seeking shopping efficiency
        
        Revenue Model:
        - Freemium model with premium features
        - Commission from affiliated retailers
        - Premium subscription: $9.99/month
        
        Initial Investment Required:
        - $500,000 for development and launch
        - $300,000 for first-year marketing
        
        Please analyze this proposal from your respective expertise areas, discuss in the business_debate channel, and vote on whether this business proposal is feasible.
        Consider market potential, financial viability, and operational challenges.
        """
    )

    # Run the collaboration
    chorus.run() 