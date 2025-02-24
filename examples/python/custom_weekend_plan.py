from chorus.agents import AsyncToolChatAgent
from chorus.teams import Team
from chorus.collaboration import DecentralizedCollaboration
from chorus.core.runner import Chorus
from chorus.teams.services.team_voting import TeamVoting
from chorus.teams.toolbox.team_voting import TeamVotingClient
from chorus.data.collaboration_strategies import DecisionMakingStrategy
from chorus.workspace.stop_conditions.message_based import MessageBasedStopper
from chorus.data.channel import Channel
from chorus.toolbox import SerperWebSearchTool, WebRetrieverToolV2
from datetime import datetime, timedelta

if __name__ == '__main__':
    # Create a channel for trip planning discussion
    planning_channel = Channel(
        name="trip_planning",
        description="Channel for team members to discuss and analyze trip options"
    )

    # Create specialized agents
    geo_expert = AsyncToolChatAgent(
        "GeoExpert",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="trip_planning" description="Channel for team members to discuss and analyze trip options"/>
        </channels>
        
        You are a geographical expert who knows the best locations for weekend trips.
        When analyzing trip options:
        1. Consider the distance and accessibility
        2. Evaluate local attractions and points of interest
        3. Consider seasonal factors and local events
        4. Share your findings in the trip_planning channel
        5. Propose specific locations with clear reasoning
        
        Keep your updates extremely concise - no more than 2-3 sentences per update.
        Focus on location-specific details and accessibility.
        Use web search to find current information about locations.""",
        tools=[SerperWebSearchTool(), WebRetrieverToolV2()]
    )

    budget_advisor = AsyncToolChatAgent(
        "BudgetAdvisor",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="trip_planning" description="Channel for team members to discuss and analyze trip options"/>
        </channels>
        
        You are a budget advisor who evaluates trip options from a cost perspective.
        When analyzing trip options:
        1. Research accommodation costs
        2. Evaluate transportation expenses
        3. Consider food and activity costs
        4. Share your findings in the trip_planning channel
        5. Focus on value for money
        
        Keep your updates extremely concise - no more than 2-3 sentences per update.
        Focus on cost-related aspects and budget considerations.
        Use web search to find current pricing information.""",
        tools=[SerperWebSearchTool(), WebRetrieverToolV2()]
    )

    experience_advisor = AsyncToolChatAgent(
        "ExperienceAdvisor",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="trip_planning" description="Channel for team members to discuss and analyze trip options"/>
        </channels>
        
        You are an experience advisor who evaluates trip options based on activities and enjoyment.
        When analyzing trip options:
        1. Research available activities
        2. Consider entertainment options
        3. Evaluate cultural experiences
        4. Share your findings in the trip_planning channel
        5. Focus on unique experiences
        
        Keep your updates extremely concise - no more than 2-3 sentences per update.
        Focus on experience quality and variety of activities.
        Use web search to find current activity information.""",
        tools=[SerperWebSearchTool(), WebRetrieverToolV2()]
    )

    safety_advisor = AsyncToolChatAgent(
        "SafetyAdvisor",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="trip_planning" description="Channel for team members to discuss and analyze trip options"/>
        </channels>
        
        You are a safety advisor who evaluates trip options from a security perspective.
        When analyzing trip options:
        1. Research local safety conditions
        2. Consider health facilities
        3. Evaluate transportation safety
        4. Share your findings in the trip_planning channel
        5. Focus on traveler security
        
        Keep your updates extremely concise - no more than 2-3 sentences per update.
        Focus on safety-related aspects and precautions.
        Use web search to find current safety information.""",
        tools=[SerperWebSearchTool(), WebRetrieverToolV2()]
    )

    planner = AsyncToolChatAgent(
        "TripPlanner",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="trip_planning" description="Channel for team members to discuss and analyze trip options"/>
        </channels>
        
        You are the main trip planner who synthesizes all advice and proposes final recommendations.
        Your role:
        1. Monitor the trip_planning channel
        2. Collect and analyze input from all advisors
        3. Consider all aspects: location, budget, experience, and safety
        4. When you have sufficient information, propose a comprehensive weekend plan
        
        When proposing a plan:
        - Wait for substantial input from all advisors
        - Keep the plan concise but detailed (maximum 8-10 sentences)
        - Structure it with clear sections: Location, Accommodation, Activities, Budget, Safety Notes
        - Include specific recommendations from each advisor
        - Propose once you see around 2-3 updates from each advisor
        
        Your proposal should be a clear, actionable weekend plan.
        Since we're using first-come-first-serve voting, your plan will be automatically accepted as the team's decision.""",
        tools=[TeamVotingClient()]
    )

    # Create team with voting service and decentralized collaboration
    planning_team = Team(
        name="WeekendPlanningTeam",
        agents=[geo_expert, budget_advisor, experience_advisor, safety_advisor, planner],
        services=[
            TeamVoting(
                decision_making_strategy=DecisionMakingStrategy.FIRST_COME_FIRST_SERVE,
                proposal_duration_seconds=600  # 10 minutes for planning
            )
        ],
        collaboration=DecentralizedCollaboration(
            time_limit=600  # 10 minutes total time limit
        )
    )

    # Create chorus runner with planning channel
    chorus = Chorus(
        teams=[planning_team],
        channels=[planning_channel],
        stop_conditions=[MessageBasedStopper(source=planning_team.get_identifier(), destination="human")],
        visual=True,
        visual_port=5000
    )

    # Calculate next weekend dates
    today = datetime.now()
    next_saturday = today + timedelta(days=(5 - today.weekday() + 7) % 7)
    next_sunday = next_saturday + timedelta(days=1)
    weekend_dates = f"{next_saturday.strftime('%m/%d/%Y')}, {next_sunday.strftime('%m/%d/%Y')}"

    # Send a trip planning request
    chorus.get_environment().send_message(
        source="human",
        destination=planning_team.get_identifier(),
        content=f"""
        Please help plan a weekend trip for the following dates: {weekend_dates}

        Location Area: San Francisco Bay Area
        Preferences:
        - Within 2-hour drive from San Francisco
        - Budget: $500-800 for the weekend
        - Interested in: Nature, hiking, local cuisine
        - Prefer safe and family-friendly areas
        
        Please analyze options and propose a detailed weekend plan considering:
        - Best location choice based on preferences
        - Accommodation recommendations
        - Activity suggestions
        - Budget breakdown
        - Safety considerations
        
        Each advisor should analyze from their perspective and share findings in the trip_planning channel.
        The planner will create a final comprehensive plan based on all inputs.
        """
    )

    # Run the collaboration
    chorus.run() 