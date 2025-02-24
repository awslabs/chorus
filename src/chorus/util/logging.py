import os

def chorus_logging_option(key: str) -> bool:
    logging_option = os.getenv("CHORUS_LOGGING", "").lower()
    logging_options = logging_option.split(",")
    return key in logging_options or "all" in logging_options