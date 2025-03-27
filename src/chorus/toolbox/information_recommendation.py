import os

from chorus.data.executable_tool import ExecutableTool
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema
from chorus.helpers.communication import CommunicationHelper


@ExecutableTool.register("InformationRecommendationTool")
class InformationRecommendationTool(SimpleExecutableTool):
    """
    An implemented tool for recommending information to user.
    """

    def __init__(self, human_name: str = "human"):
        self._human_name = human_name
        schema = {
            "tool_name": "InformationRecommendationTool",
            "name": "InformationRecommendationTool",
            "description": "A tool for recommending information to user.",
            "actions": [
                {
                    "name": "recommend",
                    "description": "Recommend information to user",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "Title of the information",
                            },
                            "summary": {
                                "type": "string",
                                "description": "Summary of the information",
                            },
                            "links": {
                                "type": "string",
                                "description": "Links to the sources of information, separated by comma",
                            },
                        },
                        "required": ["subject", "summary", "links"],
                    },
                    "output_schema": {},
                }
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))

    def recommend(self, subject: str, summary: str, links: str):
        _context = self.get_context()
        if _context is None:
            raise ValueError("MultiAgentTool requires agent context to be set.")
        verse = CommunicationHelper(_context)
        verse.send(
            destination=self._human_name,
            content="Subject: {}\nSummary: {}\nLinks: {}".format(subject, summary, links),
        )
        return {"message": f"Information recommendation sent to {self._human_name}."}
