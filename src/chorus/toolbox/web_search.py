from chorus.data.executable_tool import ExecutableTool
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema

schema = {
    "tool_name": "WebSearchTool",
    "name": "WebSearchTool",
    "description": "A tool for doing web search using DuckDuckGo API.",
    "actions": [
        {
            "name": "search",
            "description": "Search for a query.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search keywords"}},
                "required": ["query"],
            },
            "output_schema": {},
        }
    ],
}


@ExecutableTool.register("DuckDuckGoWebSearchTool")
class DuckDuckGoWebSearchTool(SimpleExecutableTool):
    """
    An implemented tool for doing web search using DuckDuckGo API.
    """

    def __init__(self):
        super().__init__(ToolSchema.model_validate(schema))

    def search(self, query: str):
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = {"results": [r for r in ddgs.text(query)]}
            return results if results else "No results found."
