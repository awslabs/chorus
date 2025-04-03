import arxiv  # type: ignore
from typing import Dict
from chorus.data.executable_tool import ExecutableTool
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema
import time

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
        import time
        
        # Add a small delay before executing the search to prevent potential rate limiting
        time.sleep(1)
        
        try:
            client = arxiv.Client()
            search = arxiv.Search(query=query, max_results=num_results)
            
            
            # Create a timeout for the search
            import threading
            import queue
            
            # Queue for results
            result_queue = queue.Queue()
            
            # Thread function to perform the search
            def perform_search():
                try:
                    results = list(client.results(search))
                    result_queue.put(("success", results))
                except Exception as e:
                    result_queue.put(("error", str(e)))
            
            # Start the search in a thread
            search_thread = threading.Thread(target=perform_search)
            search_thread.daemon = True
            search_thread.start()
            
            # Wait for results with a timeout
            timeout = 30  # 30 seconds timeout
            search_thread.join(timeout)
            
            if search_thread.is_alive():
                # Search is taking too long, return empty results
                return {"articles": [], "error": f"Search timed out after {timeout} seconds"}
            
            # Get results from queue
            if not result_queue.empty():
                status, results = result_queue.get()
                if status == "error":
                    return {"articles": [], "error": str(results)}
                
                
                response: Dict = {"articles": []}
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
            else:
                return {"articles": [], "error": "No results received from search thread"}
                
        except Exception as e:
            import traceback
            return {"articles": [], "error": str(e)}
