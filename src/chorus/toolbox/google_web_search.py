import os
from datetime import datetime
from datetime import timedelta

from chorus.data.executable_tool import ExecutableTool
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema


@ExecutableTool.register("GoogleWebSearchTool")
class GoogleWebSearchTool(SimpleExecutableTool):
    """
    An implemented tool for doing web search using Google API.
    """

    def __init__(self):
        schema = {
            "tool_name": "GoogleWebSearchTool",
            "name": "GoogleWebSearchTool",
            "description": "A tool for doing web search using Google API.",
            "actions": [
                {
                    "name": "search",
                    "description": "Search for a query",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search keywords"}
                        },
                        "required": ["query"],
                    },
                    "output_schema": {},
                }
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))

    def search(self, query: str):
        from googleapiclient.discovery import build

        api_key = os.getenv("GOOGLE_WEB_SEARCH_API_KEY", None)
        if not api_key:
            return "Error: Please provide your Google API key in the environment variable GOOGLE_WEB_SEARCH_API_KEY."
        service = build("customsearch", "v1", developerKey=api_key)
        date_string_three_month_ago = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        date_string_tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
        res = (
            service.cse()
            .list(
                q=query,
                cx="002495992715835815419:gig2feazcnw",
                sort=f"date:r:{date_string_three_month_ago}:{date_string_tomorrow}",
                num=10,
            )
            .execute()
        )
        if "items" in res:
            items = res["items"]
            results = []
            for item in items:
                result = {
                    "title": item["title"],
                    "url": item["link"],
                    "snippet": item["snippet"],
                }
                results.append(result)
            return results
        else:

            return "No results found."
