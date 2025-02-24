from jsonref import requests

from chorus.data.executable_tool import ExecutableTool
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema

schema = {
    "tool_name": "WebRetrieverTool",
    "name": "WebRetrieverTool",
    "description": "A tool for retrieving web page.",
    "actions": [
        {
            "name": "retrieve",
            "description": "Retrieve web page with a url.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The url of the web page to be retrieved.",
                    }
                },
                "required": ["url"],
            },
            "output_schema": {},
        }
    ],
}


@ExecutableTool.register("WebRetrieverTool")
class WebRetrieverTool(SimpleExecutableTool):
    """
    An implemented tool for retrieving web page.
    """

    def __init__(self):
        super().__init__(ToolSchema.model_validate(schema))

    def retrieve(self, url):
        import requests
        from bs4 import BeautifulSoup

        # Crawl the web page and extract the text, mimicking a real web browser
        # Use meta data and set timeout to 30 seconds
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, sdch, br",
            "Accept-Language": "en-US,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Referer": url,
        }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            content = response.content.decode("utf-8")
        except Exception as e:
            content = "Error:" + str(e)
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text()
        # Remove unnecessary white spaces and empty lines
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line:
                lines.append(" ".join(line.split()))
        text = "\n".join(lines)
        return text.strip()
