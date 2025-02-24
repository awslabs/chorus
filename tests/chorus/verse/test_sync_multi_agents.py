from chorus.data import Message
from chorus.agents import ToolChatAgent, SynchronizedCoordinatorAgent
from chorus.core.runner import Chorus
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
import logging

from chorus.workspace.stop_conditions import NoActivityStopper

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    sub_agents = {
            "MathExpert": "This is a MathExpert can answer your math questions."
    }
    router = SynchronizedCoordinatorAgent(
        name="Router",
        reachable_agents=sub_agents
    )
    math_expert = ToolChatAgent(
        "MathExpert",
        instruction="You are MathExpert, an expert that can answer any question about math."
    )
    team = Team(
        name="myteam",
        agents=[router.get_name(), math_expert.get_name()],
        collaboration=CentralizedCollaboration(coordinator=router.get_name())
    )
    simulator = Chorus(teams=[team], stop_conditions=[NoActivityStopper()])
    # human_input = input("Human:")
    human_input = "How to solve 3x^2 + 5 = 13?"
    simulator.get_envrionment().send_message(
        Message(source="human", destination="team:myteam", content=human_input)
    )
    simulator.run()