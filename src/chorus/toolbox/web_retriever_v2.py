import re

from jsonref import requests  # type: ignore
from chorus.data.executable_tool import SimpleExecutableTool, ExecutableTool
from chorus.data.toolschema import ToolSchema

schema = {
  "tool_name": "WebRetrieverTool",
  "name": "WebRetrieverTool",
  "description": "A tool for retrieving web page.",
  "actions": [
    {
      "name": "retrieve",
      "description": "Access and retrieve the content of a web page with a url.",
      "input_schema": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string",
            "description": "The url of the web page to be retrieved."
          }
        },
        "required": [
          "url"
        ]
      },
      "output_schema": {}
    }
  ]
}

@ExecutableTool.register("WebRetrieverToolV2")
class WebRetrieverToolV2(SimpleExecutableTool):
    """
    An implemented tool for retrieving web page.
    """

    def __init__(self):
        super().__init__(ToolSchema.model_validate(schema))

    def retrieve(self, url, max_chars=12000):
        try:
            from fake_useragent import UserAgent
            from bs4 import BeautifulSoup, NavigableString, Tag
        except ImportError:
            print("Please install the required packages: fake_useragent and beautifulsoup4")
            return None
        # Create a UserAgent object to generate a random user agent string
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            # 'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            def extract_text_with_links(element, depth=0):
                result = []
                for child in element.children:
                    if isinstance(child, NavigableString):
                        result.append(child.strip())
                    elif isinstance(child, Tag):
                        if child.name == 'a' and child.has_attr('href'):
                            link_text = child.get_text().strip()
                            href = child['href']
                            result.append(f"[{link_text}]({href})")
                        else:
                            result.extend(extract_text_with_links(child, depth + 1))
                        if depth == 0 and child.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            result.append('\n')
                return result

            if not soup.body:
                return None

            content = extract_text_with_links(soup.body)
            simplified_text = ' '.join(content).replace('\n ', '\n').strip()
            # Strip <script> and <style> tags
            simplified_text = re.sub(r'<script.*?>.*?</script>', '', simplified_text, flags=re.DOTALL)
            simplified_text = re.sub(r'<style.*?>.*?</style>', '', simplified_text, flags=re.DOTALL)

            # Truncate to max_chars if needed
            if len(simplified_text) > max_chars:
                simplified_text = simplified_text[:max_chars]

            return simplified_text

        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return None