import arxiv
from chorus.data.executable_tool import ExecutableTool
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema

schema = {
    "tool_name": "ArxivRetriever",
    "name": "ArxivRetriever",
    "description": "A tool for retrieving articles from Arxiv.",
    "actions": [
        {
            "name": "search",
            "description": "Search for articles on Arxiv, returns articles with title, authors and summary.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords"},
                    "num_results": {
                        "type": "number",
                        "description": "Number of results, optional.",
                    },
                },
                "required": ["query"],
            },
            "output_schema": {},
        }
    ],
}


@ExecutableTool.register("ArxivRetrieverTool")
class ArxivRetrieverTool(SimpleExecutableTool):
    """
    An implemented tool for retrieving information from Arxiv.
    """

    def __init__(self):
        super().__init__(ToolSchema.model_validate(schema))

    def search(self, query: str, num_results: int = 10):
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=num_results)
        results = client.results(search)
        response = {"articles": []}
        for result in results:
            response["articles"].append(
                {
                    "entry_id": result.entry_id,
                    "title": result.title,
                    "authors": [str(author) for author in result.authors],
                    "summary": result.summary,
                }
            )
        return response
