import os.path

from chorus.data import SimpleExecutableTool
from chorus.data import ToolSchema
from chorus.toolbox import schemas

SCHEMA_FOLDER = os.path.dirname(schemas.__file__)


class WeatherTool(SimpleExecutableTool):
    """
    An implemented tool for checking weather.
    """

    def __init__(self):
        super().__init__(ToolSchema.load_native_format(f"{SCHEMA_FOLDER}/examples/weather.json"))

    def get_tomorrow_weather_by_city(self, city, country, units="Fahrenheit"):
        response = {
            "data": {
                "weather": {"main": "sunny", "description": "Sunny with clear sky"},
                "temperature": {"temp": 75, "humidity": 65, "temp_max": 80, "temp_min": 60},
            },
            "status": 200,
            "message": "success",
        }
        return response

    def get_current_weather_by_city(self, city, country, units="Fahrenheit"):
        response = {
            "data": {
                "weather": {"main": "cloudy", "description": "A cloudy day"},
                "temperature": {"temp": 68, "humidity": 69, "temp_max": 72, "temp_min": 59},
            },
            "status": 200,
            "message": "success",
        }
        return response

    def current_weather_by_city(self, city, country, units="Fahrenheit"):
        response = {
            "data": {
                "weather": {"main": "cloudy", "description": "A cloudy day"},
                "temperature": {"temp": 68, "humidity": 69, "temp_max": 72, "temp_min": 59},
            },
            "status": 200,
            "message": "success",
        }
        return response
