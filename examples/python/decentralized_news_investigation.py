from chorus.agents import CollaborativeAgent
from chorus.teams import Team
from chorus.collaboration import DecentralizedCollaboration
from chorus.core.runner import Chorus
from chorus.teams.services.team_voting import TeamVoting
from chorus.teams.toolbox.team_voting import TeamVotingClient
from chorus.data.collaboration_strategies import DecisionMakingStrategy
from chorus.workspace.stop_conditions.message_based import MessageBasedStopper
from chorus.data.channel import Channel
from chorus.toolbox import SerperWebSearchTool, WebRetrieverToolV2

if __name__ == '__main__':
    # Create channels for different aspects of investigation
    investigation_channel = Channel(
        name="investigation_updates",
        description="Channel for sharing investigation findings and updates"
    )

    # Create investigator agents for different aspects
    fact_checker = CollaborativeAgent(
        "FactChecker",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="investigation_updates" description="Channel for sharing investigation findings and updates"/>
        </channels>
        
        You are a fact-checking investigator who verifies factual claims in news stories.
        When investigating a news topic:
        1. Search for primary sources and official records
        2. Verify dates, numbers, and specific claims
        3. Cross-reference information from multiple sources
        4. Share your findings in the investigation_updates channel
        5. Highlight any discrepancies or corrections
        6. Focus on accuracy and verification
        7. Research up to 1 page of sources, pick the most relevant ones.
        
        Keep your updates extremely concise - no more than 2-3 sentences per update.
        Focus on key facts and verification status.
        Use both web search and web retrieval to gather comprehensive information.""",
        tools=[SerperWebSearchTool()]
    )

    main_news_investigator = CollaborativeAgent(
        "MainNewsInvestigator",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="investigation_updates" description="Channel for sharing investigation findings and updates"/>
        </channels>
        
        You are the main news investigator who deeply investigates the core content of the news topic.
        When investigating a news topic:
        1. Focus on the main story and its key details
        2. Investigate who is involved and what exactly happened
        3. Research the immediate impact and reactions
        4. Share your findings in the investigation_updates channel
        5. Identify the most newsworthy elements
        6. Verify the sequence of events
        7. Research up to 1 page of sources, pick the most relevant ones.

        Keep your updates extremely concise - no more than 2-3 sentences per update.
        Focus on the most important aspects of the story.
        Use both web search and web retrieval to gather comprehensive information.""",
        tools=[SerperWebSearchTool()]
    )

    source_analyzer = CollaborativeAgent(
        "SourceAnalyzer",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="investigation_updates" description="Channel for sharing investigation findings and updates"/>
        </channels>
        
        You are a source analyzer who evaluates the credibility and perspective of news sources.
        When investigating a news topic:
        1. Analyze source credibility and bias
        2. Compare coverage across different outlets
        3. Identify potential conflicts of interest
        4. Share your findings in the investigation_updates channel
        5. Evaluate source expertise and authority
        6. Note any media bias or agenda
        7. Research up to 1 page of sources, pick the most relevant ones.
        Keep your updates extremely concise - no more than 2-3 sentences per update.
        Focus on key findings about source reliability.
        Use both web search and web retrieval to gather comprehensive information.""",
            tools=[SerperWebSearchTool()]
    )

    summarizer = CollaborativeAgent(
        "Summarizer",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="investigation_updates" description="Channel for sharing investigation findings and updates"/>
        </channels>
        
        You are a news summarizer who monitors the investigation and proposes comprehensive summaries.
        Your role:
        1. Monitor the investigation_updates channel
        2. Collect and analyze findings from all investigators
        4. When you think enough information has been gathered, propose a comprehensive summary
        5. Include verified facts, main story details, and source analysis in your summary

        When proposing a summary:
        - Keep the summary concise and focused (maximum 5-6 sentences)
        - Structure it with clear bullet points
        - Highlight the most important verified facts
        - Include any critical caveats or uncertainties
        - Do not wait for too long, propose a summary once there are around 5 rounds of updates.
        
        Your proposal should be a clear, concise summary of the key findings.
        Since we're using first-come-first-serve voting, your summary will be automatically accepted as the team's decision.""",
        tools=[TeamVotingClient()]
    )

    # Create team with voting service and decentralized collaboration
    investigation_team = Team(
        name="NewsInvestigationTeam",
        agents=[fact_checker, main_news_investigator, source_analyzer, summarizer],
        services=[
            TeamVoting(
                decision_making_strategy=DecisionMakingStrategy.FIRST_COME_FIRST_SERVE,
                proposal_duration_seconds=600  # 10 minutes for investigation
            )
        ],
        collaboration=DecentralizedCollaboration(
            time_limit=600  # 10 minutes total time limit
        )
    )

    # Create chorus runner with investigation channel
    chorus = Chorus(
        teams=[investigation_team],
        channels=[investigation_channel],
        stop_conditions=[MessageBasedStopper(source=investigation_team.get_identifier(), destination="human")],
        visual=True,
        visual_port=5000
    )

    # Send a news topic for investigation
    chorus.get_environment().send_message(
        source="human",
        destination=investigation_team.get_identifier(),
        content="""
        Please investigate this news topic:

        "OpenAI Announces GPT-5: Claims Major Breakthrough in Reasoning Capabilities"

        Investigate this news story from multiple angles:
        - Verify the factual claims and timeline
        - Explore the context of AI development and previous GPT models
        - Analyze the credibility of sources reporting this news
        
        The summarizer should propose a comprehensive summary once sufficient investigation has been conducted.
        """
    )

    # Run the collaboration
    chorus.run() 