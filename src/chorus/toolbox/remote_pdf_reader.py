import json
import os
from datetime import datetime, timedelta
from typing import Optional
import io

import requests
from chorus.data.executable_tool import SimpleExecutableTool, ExecutableTool
from chorus.data.toolschema import ToolSchema

@ExecutableTool.register("RemotePDFReaderTool")
class RemotePDFReaderTool(SimpleExecutableTool):
    """
    An implemented tool for reading PDF files.
    """
    def __init__(self):
        try:
            import pdfplumber
        except:
            raise ValueError("Error: Please install pdfplumber package to use this tool.")
        schema = {
            "tool_name": "RemotePDFReaderTool",
            "name": "RemotePDFReaderTool",
            "description": "A tool for reading PDF files.",
            "actions": [
                {
                    "name": "read",
                    "description": "Read a PDF file",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL of the PDF file"
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
        super().__init__(ToolSchema.model_validate(schema))

    def read(self, url: str):
        import pdfplumber
        response = requests.get(url)
        if response.status_code == 200:
            pdf = io.BytesIO(response.content)
            with pdfplumber.open(pdf) as pdf_file:
                content = ""
                for i, page in enumerate(pdf_file.pages[:10]):
                    content += f"### Page {i + 1} ###\n\n"
                    text = page.extract_text(x_tolerance=1)
                    tables = page.extract_tables()
                    for table in tables:
                        content += "Table:\n" + str(table) + "\n\n"
                    content += text
                content = content.strip()
                return content
        else:
            return f"Error: Failed to fetch PDF file from {url}."
