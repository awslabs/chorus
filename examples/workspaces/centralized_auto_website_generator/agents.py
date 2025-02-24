import os
import uuid

from chorus.data import ToolSchema, SimpleExecutableTool, ExecutableTool

schema = {
  "tool_name": "WebsiteDeploymentTool",
  "name": "WebsiteDeploymentTool",
  "description": "A tool for deploying a prototype website.",
  "actions": [
    {
      "name": "deploy",
      "description": "Deploy a prototype website with simple html, javascript and css files. Return a link to visit the deployed website.",
      "input_schema": {
        "type": "object",
        "properties": {
          "html": {
            "type": "string",
            "description": "Content of the html."
          },
            "css": {
                "type": "string",
                "description": "Content of the css."
            },
            "javascript": {
                "type": "string",
                "description": "Content of the javascript."
            }
        },
        "required": [
          "html",
          "css",
          "javascript"
        ]
      },
      "output_schema": {
          "type": "string"
      }
    }
  ]
}

@ExecutableTool.register("WebsiteDeploymentTool")
class WebsiteDeploymentTool(SimpleExecutableTool):

    def __init__(self):
        super().__init__(ToolSchema.model_validate(schema))

    def deploy(self, html: str, css: str, javascript: str) -> str:
        html = html.strip("`")
        css = css.strip("`")
        javascript = javascript.strip("`")
        html = html.replace("<head>", f"<head><style>{css}</style>")
        html = html.replace("</body>", f"<script>{javascript}</script></body>")
        random_file_token = uuid.uuid4().hex
        home_dir = os.path.expanduser("~")
        with open(f"{home_dir}/agent_artifacts/{random_file_token}.html", "w") as f:
            f.write(html)
        return f"Link to visit the deployed website: https://agentverse.ai.aws.dev/agent_artifacts/{random_file_token}.html"


