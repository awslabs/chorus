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
    # Create a team channel for agent communication
    team_channel = Channel(
        name="team_discussion",
        description="Channel for team members to discuss proposals and share thoughts"
    )

    # Create agents with voting tool
    agent1 = AsyncToolChatAgent(
        "Agent1",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="team_discussion" description="Channel for team members to discuss proposals and share thoughts"/>
        </channels>
        You are a collaborative agent that can propose solutions and vote on them.
        When you receive a task:
        1. Share your initial thoughts in the team_discussion channel
        2. Propose a solution that you think is best
        3. Monitor the team_discussion channel for other agents' thoughts
        4. When you see other proposals, evaluate them and share your thoughts in the team_discussion channel
        5. Vote for the proposal you think is best
        6. Make your message content as short as possible. No more than 2 sentences.
        Always explain your reasoning when proposing or voting.
        Make sure to actively participate in team discussions.""",
        tools=[TeamVotingClient()]
    )

    agent2 = AsyncToolChatAgent(
        "Agent2",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="team_discussion" description="Channel for team members to discuss proposals and share thoughts"/>
        </channels>
        You are a collaborative agent that can propose solutions and vote on them.
        When you receive a task:
        1. Share your initial thoughts in the team_discussion channel
        2. Read other agents' thoughts in the team_discussion channel
        3. Propose a different solution than what others have suggested
        4. Engage in discussion about the pros and cons of each proposal
        5. Vote for the proposal you think is best
        6. Make your message content as short as possible. No more than 2 sentences.
        Try to propose different solutions than others.
        Always explain your reasoning when proposing or voting.
        Actively participate in team discussions and respond to others' points.""",
        tools=[TeamVotingClient()]
    )

    agent3 = AsyncToolChatAgent(
        "Agent3",
        instruction="""
        Here are the channels available for communication:
        <channels>
        <channel name="team_discussion" description="Channel for team members to discuss proposals and share thoughts"/>
        </channels>
        You are a collaborative agent that can propose solutions and vote on them.
        When you receive a task:
        1. Share your initial analysis in the team_discussion channel
        2. Focus on practical and efficient solutions
        3. Critically evaluate other proposals and share your analysis
        4. Propose your solution after considering others' input
        5. Vote for the most practical and efficient proposal
        6. Make your message content as short as possible. No more than 2 sentences.
        Focus on practical and efficient solutions.
        Always explain your reasoning when proposing or voting.
        Engage in constructive discussion about the trade-offs of each proposal.""",
        tools=[TeamVotingClient()]
    )

    # Create team with voting service and decentralized collaboration
    team = Team(
        name="DecisionMakingTeam",
        agents=[agent1, agent2, agent3],
        services=[
            TeamVoting(
                decision_making_strategy=DecisionMakingStrategy.MAJORITY_VOTE,
                proposal_duration_seconds=300  # 5 minutes duration for example
            )
        ],
        collaboration=DecentralizedCollaboration(
            time_limit=300  # 5 minutes total time limit
        )
    )

    # Create chorus runner with team channel
    chorus = Chorus(
        teams=[team],
        channels=[team_channel],
        stop_conditions=[MessageBasedStopper(source=team.get_identifier(), destination="human")],
        visual=True,
        visual_port=5000
    )

    # Send a task to the team
    chorus.get_environment().send_message(
        source="human",
        destination=team.get_identifier(),
        content="""
        We need to decide on a programming language for our new microservices project.
        The requirements are:
        1. Good performance
        2. Strong ecosystem
        3. Easy to hire developers
        4. Good for microservices
        
        Please discuss the options as a team in the team_discussion channel, propose solutions, and vote on the best choice.
        Make sure to consider each other's perspectives and explain your reasoning.
        """
    )

    # Run the collaboration
    chorus.run() 