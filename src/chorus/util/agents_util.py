import uuid

def generate_agent_id(agent_class_name: str):
    """
    Generate a unique agent ID based on the agent class name.
    """

    return f"{agent_class_name}_{uuid.uuid4().hex[:6]}"