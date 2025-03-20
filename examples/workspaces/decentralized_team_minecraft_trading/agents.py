import json
import uuid
from typing import Optional, Dict

from jinja2 import Template
from pydantic import BaseModel

from chorus.agents import Agent, ClaudeATaskCoordinatorAgent
from chorus.data.state import PassiveAgentState
from chorus.helpers.communication import CommunicationHelper
from chorus.data import Message, AgentContext, AgentState, SimpleExecutableTool, ToolSchema
from chorus.agents import PassiveAgent

from datetime import datetime

TRADING_PROPOSAL_MESSAGE = """
You received a trading offer from {{source_agent}} with trade ID: {{trade_id}}, who offers following items:

{{offer}}

As return, {{source_agent}} asks for following items:

{{ask_for}}

If you accept this offer, please call confirm_trade function with above trade ID.
""".strip()


class Trade(BaseModel):
    source_agent: str
    opponent: str
    offer: Dict[str, int]
    ask_for: Dict[str, int]

class MinecraftTradingAdminState(PassiveAgentState):
    current_inventory: Dict[str, Dict[str, int]]
    proposed_trades: Dict[str, Trade]
    current_interation: int = 0

@Agent.register("MinecraftTradingAdmin")
class MinecraftTradingAdminAgent(PassiveAgent):

    def __init__(self, name, organizer_name, players, initial_inventory):
        super().__init__(name)
        self.name = name
        self.organizer_name = organizer_name
        self.players = players
        self.initial_inventory = initial_inventory

    def init_state(self) -> MinecraftTradingAdminState:
        return MinecraftTradingAdminState(current_inventory=self.initial_inventory, proposed_trades={})

    def _generate_trade_ID(self):
        return uuid.uuid4().hex

    def respond(self, context: AgentContext, state: MinecraftTradingAdminState, inbound_message: Message) -> MinecraftTradingAdminState:
        verse = CommunicationHelper(context)

        message_content = inbound_message.content
        source_agent = inbound_message.source
        json_content = None
        try:
            json_content = json.loads(message_content)
        except json.JSONDecodeError:
            verse.send(destination=source_agent, content=json.dumps({"error": "Invalid JSON format."}))
            return state

        if "action" not in json_content or "parameters" not in json_content:
            verse.send(destination=source_agent, content=json.dumps({"error": "Missing action or parameters in JSON content."}))
            return state

        action_name = json_content["action"]
        parameters = json_content["parameters"]

        if action_name == "get_inventory":
            return_message_content = "Your current inventory:\n" + json.dumps(state.current_inventory.get(source_agent))
            verse.send(destination=source_agent, content=return_message_content)
            return state

        if action_name == "get_all_inventory" and source_agent == self.organizer_name:
            verse.send(destination=source_agent, content=json.dumps(state.current_inventory, indent=4))
            return state

        if action_name == "propose_trade":
            offer = parameters.get("offer", {})
            ask_for = parameters.get("ask_for", {})
            if type(offer) is str:
                offer = json.loads(offer)
            if type(ask_for) is str:
                ask_for = json.loads(ask_for)
            trading_opponent = parameters.get("opponent", "")
            for item_name, item_quantity in offer.items():
                if item_name not in state.current_inventory.get(source_agent, {}):
                    verse.send(destination=source_agent, content=json.dumps({"error": f"You don't have {item_name} in your inventory."}))
                    return state
                if int(item_quantity) > int(state.current_inventory.get(source_agent, {})[item_name]):
                    verse.send(destination=source_agent, content=json.dumps({"error": f"You don't have enough {item_name} in your inventory."}))
                    return state
            trade_id = self._generate_trade_ID()
            state.proposed_trades[trade_id] = Trade(source_agent=source_agent, opponent=trading_opponent, offer=offer, ask_for=ask_for)
            verse.send(destination=trading_opponent, content=Template(TRADING_PROPOSAL_MESSAGE, autoescape=True).render( # from jinja2 import Template
                source_agent=source_agent,
                trade_id=trade_id,
                offer=json.dumps(offer),
                ask_for=json.dumps(ask_for)
            ))
            verse.send(destination=source_agent, content=json.dumps({"status": "The trade offer has been sent to the trading opponent."}))
            return state

        if action_name == "confirm_trade":
            trade_id = parameters.get("trade_id", "")
            if trade_id not in state.proposed_trades:
                verse.send(destination=source_agent, content=json.dumps({"error": f"Invalid trade ID: {trade_id}."}))
                return state
            trade = state.proposed_trades[trade_id]
            state.proposed_trades.pop(trade_id)
            if source_agent != trade.opponent:
                verse.send(destination=source_agent, content=json.dumps({"error": f"You are not the opponent of this trade."}))
                return state
            for item_name, item_quantity in trade.ask_for.items():
                if item_name not in state.current_inventory.get(trade.opponent, {}):
                    verse.send(destination=source_agent, content=json.dumps({"error": f"You don't have {item_name} in inventory."}))
                    return state
                if int(item_quantity) > int(state.current_inventory.get(trade.opponent, {})[item_name]):
                    verse.send(destination=source_agent, content=json.dumps({"error": f"You don't have enough {item_name} in inventory."}))
                    return state
            for item_name, item_quantity in trade.offer.items():
                if item_name not in state.current_inventory.get(trade.source_agent, {}):
                    verse.send(destination=source_agent, content=json.dumps({"error": f"{trade.source_agent} doesn't have {item_name} in its inventory."}))
                    return state
                if int(item_quantity) > int(state.current_inventory.get(trade.source_agent, {})[item_name]):
                    verse.send(destination=source_agent, content=json.dumps({"error": f"{trade.source_agent} doesn't have enough {item_name} in its inventory."}))
                    return state
            # All good, execute the trade
            for item_name, item_quantity in trade.offer.items():
                state.current_inventory[trade.source_agent][item_name] = state.current_inventory[trade.source_agent][item_name] - item_quantity
                state.current_inventory[trade.opponent][item_name] = state.current_inventory[trade.opponent].get(item_name, 0) + item_quantity
            for item_name, item_quantity in trade.ask_for.items():
                state.current_inventory[trade.opponent][item_name] = state.current_inventory[trade.opponent][item_name] - item_quantity
                state.current_inventory[trade.source_agent][item_name] = state.current_inventory[trade.source_agent].get(item_name, 0) + item_quantity
            verse.send(destination=trade.opponent, content=json.dumps({"status": f"The trade {trade_id} has been executed. Your current inventory is:\n{json.dumps(state.current_inventory.get(trade.opponent))}."}))
            verse.send(destination=trade.source_agent, content=json.dumps({"status": f"The trade {trade_id} has been executed. Your current inventory is:\n{json.dumps(state.current_inventory.get(trade.source_agent))}."}))
            return state

        verse.send(destination=source_agent, content=json.dumps({"error": f"Invalid action: {action_name}."}))
        return state

@Agent.register("MinecraftOrganizer")
class MinecraftOrganizer(PassiveAgent):

    def __init__(self, name, admin_name, players, num_iterations=10):
        super().__init__(name)
        self.name = name
        self.admin_name = admin_name
        self.players = players
        self.num_iterations = num_iterations

    def respond(self, context: AgentContext, state: PassiveAgentState, inbound_message: Message) -> PassiveAgentState:
        verse = CommunicationHelper(context)
        message_content = inbound_message.content
        source_agent = inbound_message.source
        if source_agent != "human" or message_content != "start game":
            if source_agent == "human":
                verse.send(destination=source_agent, content=f"Invalid message. Please start the game by sending 'start game' to the {self.name}.")
            return state

        for i in range(self.num_iterations):
            current_inventory = verse.send_and_wait(
                destination=self.admin_name,
                content=json.dumps({"action": "get_all_inventory", "parameters": {}})
            ).content
            verse.send(
                destination="human",
                content="Start Iteration: {} / {}. Current Inventories:\n {}".format(
                    i+1,
                    self.num_iterations,
                    current_inventory
                )
            )
            inventories = json.loads(current_inventory)
            for player in self.players:
                verse.send(destination=player, content=f"Start Iteration: {i+1} / {self.num_iterations}.")
                verse.send(destination=player, content=f"Your current inventory:\n{inventories.get(player, {})}")

            for player in self.players:
                verse.wait(source=player)

        verse.send(destination="human", content="Simulation has ended")
        current_inventory = verse.send_and_wait(
            destination=self.admin_name,
            content=json.dumps({"action": "get_all_inventory", "parameters": {}})
        ).content
        verse.send(
            destination="human",
            content="Final Inventories:\n {}".format(
                current_inventory
            )
        )
        return state

class MinecraftTradingTool(SimpleExecutableTool):

    def __init__(self, admin_agent: str):
        schema = {
            "tool_name": "TradingTool",
            "name": "TradingTool",
            "description": "A tool for trading items in Minecraft",
            "actions": [
                {
                    "name": "get_inventory",
                    "description": "Check the items and quantities in inventory",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    },
                    "output_schema": {}
                },
                {
                    "name": "propose_trade",
                    "description": "Propose a trade with another player. ",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "offer": {
                                "type": "object",
                                "description": "The items you offer to the other player. Must be a dictionary of item name : item quantity pairs",
                                "properties": {
                                    "item_name": {
                                        "type": "string"
                                    },
                                    "item_quantity": {
                                        "type": "integer"
                                    }
                                },
                                "required": ["item_name", "item_quantity"]
                            },
                            "ask_for": {
                                "type": "object",
                                "description": "The items you ask for from the other player. Must be a dictionary of item name : item quantity pairs. ",
                                "properties": {
                                    "item_name": {
                                        "type": "string"
                                    },
                                    "item_quantity": {
                                        "type": "integer"
                                    }
                                },
                                "required": ["item_name", "item_quantity"]
                            },
                            "opponent": {
                                "type": "string",
                                "description": "The name of the other player"
                            }
                        },
                        "required": ["offer", "ask_for", "opponent"]
                    },
                    "output_schema": {}
                }
            ]
        }
        self._admin_agent = admin_agent
        super().__init__(ToolSchema.model_validate(schema))

    def get_inventory(self) -> str:
        if self.get_context() is None:
            raise ValueError("MultiAgentTool requires agent context to be set.")
        verse = CommunicationHelper(self.get_context())
        verse.send(
            destination=self._admin_agent,
            content=json.dumps({"action": "get_inventory", "parameters": {}})
        )
        return verse.wait(source=self._admin_agent).content

    def propose_trade(self, offer: Dict[str, int], ask_for: Dict[str, int], opponent: str) -> str:
        if self.get_context() is None:
            raise ValueError("MultiAgentTool requires agent context to be set.")
        verse = CommunicationHelper(self.get_context())
        verse.send(
            destination=self._admin_agent,
            content=json.dumps({"action": "propose_trade", "parameters": {"offer": offer, "ask_for": ask_for, "opponent": opponent}})
        )
        return verse.wait(source=self._admin_agent).content

    def confirm_trade(self, trade_id: str) -> str:
        if self.get_context() is None:
            raise ValueError("MultiAgentTool requires agent context to be set.")
        verse = CommunicationHelper(self.get_context())
        verse.send(
            destination=self._admin_agent,
            content=json.dumps({"action": "confirm_trade", "parameters": {"trade_id": trade_id}})
        )
        return verse.wait(source=self._admin_agent).content


@Agent.register("MinecraftPlayer")
class MinecraftPlayer(ClaudeATaskCoordinatorAgent):

    def __init__(self, name, players, organizer_name, admin_name, instruction=None):
        self.name = name
        self.players = players
        self.organizer_name = organizer_name
        self.admin_name = admin_name
        reachable_agents = {}
        for player in players:
            if player == name:
                continue
            reachable_agents[player] = f"This is another player in the trading game: {player}."
        super().__init__(
            name,
            reachable_agents=reachable_agents,
            tools=[MinecraftTradingTool(admin_agent=admin_name)],
            instruction=instruction,
            allow_waiting=False
        )

    def respond(self, context: AgentContext, state: PassiveAgentState, inbound_message: Message) -> PassiveAgentState:
        verse = CommunicationHelper(context)
        if inbound_message.source != self.organizer_name:
            return state
        try:
            super().respond(context, state, inbound_message)
        except ValueError as e:
            pass
        verse.send(
            destination=self.organizer_name,
            content=f"Player {self.name} has finished this iteration."
        )
        return state
