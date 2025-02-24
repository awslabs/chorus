import os

from chorus.data.executable_tool import ExecutableTool
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema


@ExecutableTool.register("WeatherCheckingTool")
class WeatherCheckingTool(SimpleExecutableTool):
    """
    An implemented tool for checking weather information.
    """

    def __init__(self):
        schema = {
            "tool_name": "WeatherCheckingTool",
            "name": "WeatherCheckingTool",
            "description": "A tool for checking weather information.",
            "actions": [
                {
                    "name": "check_weather",
                    "description": "Check the weather information",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The location to check the weather",
                            }
                        },
                        "required": ["location"],
                    },
                    "output_schema": {},
                }
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))

    def check_weather(self, location: str):
        import requests

        api_key = os.getenv("OPENWEATHERMAP_API_KEY", None)
        if not api_key:
            return "Error: Please provide your OpenWeatherMap API key in the environment variable OPENWEATHERMAP_API_KEY."
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return "Error: Failed to get weather information."
