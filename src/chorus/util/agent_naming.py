import uuid


def get_unique_agent_name() -> str:
    """
    Generate a unique agent name.

    Returns:
        str: A unique agent name in the format 'agent_<6 hex chars>'
    """
    # Generate a random UUID and take first 6 characters of its hex representation
    unique_id = str(uuid.uuid4()).replace('-', '')[:6]
    return f"agent_{unique_id}"