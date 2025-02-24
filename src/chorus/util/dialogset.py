TURN_TYPE_MAPPING = {
    "USER_TO_BOT": "User",
    "BOT_TO_API": "Action",
    "API_TO_BOT": "Observation",
    "BOT_TO_USER": "Bot",
    "BOT_TO_SELF": "Thought",
}


def update_dialogset_schema(json_data):
    dialogs = json_data["dialogs"]
    for dialog in dialogs:
        turns = dialog["turns"]
        updated_turns = []
        for turn in turns:
            turn_type = turn["turn_type"]
            role = TURN_TYPE_MAPPING[turn_type]
            del turn["turn_type"]
            turn["role"] = role
            if role == "Action":
                old_content = turn["content"]
                turn["actions"] = [
                    {
                        "tool_name": old_content["tool_id"],
                        "action_name": old_content["action_name"],
                        "parameters": old_content["action_args"],
                    }
                ]
                turn["content"] = None
            elif role == "Observation":
                old_content = turn["content"]
                turn["observation"] = old_content["value"]
                turn["content"] = None
            else:
                turn["actions"] = None
                turn["observation"] = None
            updated_turns.append(turn)
        dialog["turns"] = updated_turns
    # Update tools
    for tool in json_data["tool_db"]["tools"]:
        tool["tool_name"] = tool["tool_id"]
        del tool["tool_id"]
