from typing import Optional

from chorus.agents import Agent
from chorus.data.state import PassiveAgentState
from chorus.helpers.communication import CommunicationHelper
from chorus.data import Message, AgentContext, AgentState
from chorus.agents import PassiveAgent

from datetime import datetime

@Agent.register("MyTripCityRecommendationAgent")
class MyTripCityRecommendationAgent(PassiveAgent):

    def __init__(self, name, geo_expert, advisors):
        super().__init__(name)
        self.geo_expert_name = geo_expert
        self.advisor_names = advisors

    def respond(self, context: AgentContext, state: PassiveAgentState, inbound_message: Message) -> PassiveAgentState:
        verse = CommunicationHelper(context)
        if inbound_message.source != "human":
            return state
        if not verse.smart_judge(inbound_message.content, "contains a city or a specific location"):
            verse.send(
                destination="human",
                content="Please indicate a location where you want to plan a trip nearby this weekend."
            )
            return state
        weekend_dates = verse.prompt(f"Today is {datetime.now().strftime('%m/%d/%Y')}. Generate dates of next Saturday and next Sunday. Return the dates in MM/DD/YYY, MM/DD/YYY format with nothing else.")
        verse.send(
            destination='human',
            content=f"I'm now working on finding best city for your trip for this weekend ({weekend_dates}), it might take a while..."
        )
        verse.send(
            destination=self.geo_expert_name,
            content=f"Suggest the 10 candidate nearby locations for a weekend strip based on following description,"
                    f" please list only location names in bullet points with nothing else:\n{inbound_message.content}"
        )
        geo_message = verse.wait(
            source=self.geo_expert_name,
        )
        locations = verse.smart_extract(geo_message.content, "a list of locations in bullet points")
        verse.send(
            destination='human',
            content=f"I have obtained a list of candidates, now I'm reviewing these options.\n\nCandidate locations:\n{locations}"
        )
        verse.send(destination="WeatherInvestigationAgent", content=f"Dates: {weekend_dates}\n\nLocations: {locations}")
        for advisor in self.advisor_names:
            verse.send(
                destination=advisor,
                content=f"Review following locations for a trip, provide review for each location in bullet points and provide a final recommendation:\n"
                        f"{locations}"
            )
        advices = []
        for advisor in self.advisor_names:
            response = verse.wait(
                source=advisor
            )
            advices.append(f"{advisor}: {response.content}")
        weather_report = verse.wait(
            source="WeatherInvestigationAgent"
        )
        verse.send(
            destination='human',
            content=f"I have obtained all reviews and weather information. Now I'm summarizing into a final recommendation."
        )
        combined_advice = '\n\n'.join(advices)
        verse.send(
            destination=self.geo_expert_name,
            content=f"User request:\n{inbound_message.content}\n\nFor above request, you previously suggested following cities for a trip:\n{locations}\n\n"
                    f"You have received following reviews:\n\n{combined_advice}\n\n"
                    f"Here is the weather information for these locations:\n\n{weather_report.content}\n\n"
                    f"Based on above information, please pick and suggest one city for trip and give reason that considers the review."
        )
        response = verse.wait(
            source=self.geo_expert_name
        )
        verse.send(
            destination="human",
            content=response.content
        )
        return state