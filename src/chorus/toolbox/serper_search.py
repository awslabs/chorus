import json
import os
from datetime import datetime, timedelta
from typing import Optional

import requests
from chorus.data.executable_tool import SimpleExecutableTool, ExecutableTool
from chorus.data.toolschema import ToolSchema

@ExecutableTool.register("SerperWebSearchTool")
class SerperWebSearchTool(SimpleExecutableTool):
    """
    An implemented tool for doing web search using Google API.
    """

    def __init__(self):
        self._api_key = os.getenv("SERPER_WEB_SEARCH_API_KEY", None)
        if not self._api_key:
            raise ValueError("Error: Please provide your Serper API key in the environment variable SERPER_WEB_SEARCH_API_KEY.")
        self._search_prefix = None
        schema = {
            "tool_name": "WebSearchTool",
            "name": "WebSearchTool",
            "description": "A tool for doing web search using Google API.",
            "actions": [
                {
                    "name": "search",
                    "description": "Search for a query",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search keywords"
                            }
                        },
                        "required": [
                            "query"
                        ]
                    },
                    "output_schema": {}
                }
            ]
        }
        super().__init__(ToolSchema.model_validate(schema))

    def set_search_prefix(self, prefix: Optional[str]):
        self._search_prefix = prefix

    def search(self, query: str):
        if not self._api_key:
            return "Error: Please provide your Serper API key in the environment variable SERPER_WEB_SEARCH_API_KEY."

        url = "https://google.serper.dev/search"

        if self._search_prefix:
            query = f"{self._search_prefix} {query}"

        payload = json.dumps({
            "q": query,
            "tbs": "qdr:m"
        })
        headers = {
            'X-API-KEY': self._api_key,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            res = json.loads(response.text)
        except:
            return "Error: Invalid response from Serper API."
        if "organic" in res:
            items = res["organic"]
            results = []
            for item in items:
                result = {
                    "title": item["title"],
                    "url": item["link"],
                    "snippet": item["snippet"],
                    "date": item.get("date", None)
                }
                results.append(result)
            return {"results": results}
        else:

            return "No results found."
