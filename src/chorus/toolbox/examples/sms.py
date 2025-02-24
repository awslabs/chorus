import os.path

from chorus.data import SimpleExecutableTool
from chorus.data import ToolSchema
from chorus.toolbox import schemas

SCHEMA_FOLDER = os.path.dirname(schemas.__file__)


class SMSTool(SimpleExecutableTool):
    """
    An implemented tool for sending SMS.
    """

    def __init__(self):
        super().__init__(ToolSchema.load_native_format(f"{SCHEMA_FOLDER}/examples/sms.json"))

    def send_sms(self, message, to):
        response = {
            "data": {
                "messages": [
                    {
                        "to": "+1.206603012",
                        "status": "sent",
                        "message-price": "$0.05",
                        "remaining-balance": "$14.95",
                    }
                ],
                "message-count": "1",
            },
            "status": 200,
            "message": "success",
        }
        return response
