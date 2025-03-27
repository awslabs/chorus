from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from chorus.data.state import TeamState
from chorus.data.data_types import ObservationData
from chorus.data.dialog import Message
from chorus.data.context import TeamContext
from chorus.teams.services.base import TeamService

@dataclass
class LineInfo:
    content: str
    last_modified_by: str
    last_modified_time: datetime

@TeamService.register("TeamScratchpad")
class TeamScratchpad(TeamService):
    def __init__(self):
        super().__init__("team_scratchpad")

    def initialize_service(self, team_state: TeamState):
        data_store = team_state.get_service_data_store(self.get_name())
        # Initialize empty scratchpads dictionary
        # Structure: {scratchpad_id: List[LineInfo]}
        data_store["scratchpads"] = {}

    def process_message(self, team_context: TeamContext, team_state: TeamState, inbound_message: Message):
        if inbound_message.event_type != "team_service":
            return
            
        data_store = team_state.get_service_data_store(self.get_name())
        observations = []
        if inbound_message.actions is None:
            return
        for action in inbound_message.actions:
            if action.tool_name == self.get_name():
                if action.action_name == "create_scratchpad":
                    scratchpad_id = action.parameters.get("scratchpad_id")
                    if scratchpad_id not in data_store["scratchpads"]:
                        data_store["scratchpads"][scratchpad_id] = []
                    observations.append(
                        ObservationData(
                            data=f"Created scratchpad {scratchpad_id}"
                        )
                    )
                
                elif action.action_name == "get_scratchpad":
                    scratchpad_id = action.parameters.get("scratchpad_id")
                    if scratchpad_id in data_store["scratchpads"]:
                        content = {
                            "lines": [
                                f"L{i}: {line.content}" for i, line in enumerate(data_store["scratchpads"][scratchpad_id])
                            ]
                        }
                        observations.append(ObservationData(data=content))
                    else:
                        observations.append(ObservationData(data={"error": "Scratchpad not found"}))
                
                elif action.action_name == "edit_lines":
                    scratchpad_id = action.parameters.get("scratchpad_id")
                    start_line = action.parameters.get("start_line_number", 0)
                    end_line = action.parameters.get("end_line_number", 0) 
                    new_content = action.parameters.get("new_content", "")
                    editor = action.parameters.get("editor", "")
                    
                    if scratchpad_id not in data_store["scratchpads"]:
                        observations.append(ObservationData(data={"error": "Scratchpad not found"}))
                        continue
                        
                    scratchpad = data_store["scratchpads"][scratchpad_id]
                    
                    # Split content into lines
                    new_lines = new_content.splitlines(keepends=False)
                    new_line_infos = [
                        LineInfo(
                            content=line,
                            last_modified_by=editor,
                            last_modified_time=datetime.now()
                        ) for line in new_lines
                    ]
                    new_scratchpad = scratchpad[:start_line] + new_line_infos + scratchpad[end_line + 1:]
                    
                    # Insert new lines at the same position
                    data_store["scratchpads"][scratchpad_id] = new_scratchpad
                    observations.append(
                        ObservationData(
                            data={
                                "message": f"Updated lines {start_line} to {end_line}",
                                "lines": [
                                    f"L{i}: {line.content}" for i, line in enumerate(new_scratchpad)
                                ]
                            }
                        )
                    )
                    
                elif action.action_name == "delete_scratchpad":
                    scratchpad_id = action.parameters.get("scratchpad_id")
                    if scratchpad_id in data_store["scratchpads"]:
                        del data_store["scratchpads"][scratchpad_id]
                        observations.append(
                            ObservationData(
                                data=f"Deleted scratchpad {scratchpad_id}"
                            )
                        )
                    else:
                        observations.append(ObservationData(data={"error": "Scratchpad not found"}))

        if observations:
            outbound_event = Message(
                destination=inbound_message.source,
                observations=observations
            )
            team_context.message_service.send_message(outbound_event)