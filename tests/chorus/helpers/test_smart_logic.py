import unittest
from unittest.mock import MagicMock
from chorus.data.context import AgentContext
from chorus.helpers.smart_logic import SmartLogicHelper

def mock_generate(prompt, **kwargs):
    if "Michael Jordan is a retired professional basketball player. He is widely regarded as one of the greatest basketball players of all time." in prompt.to_dict()["messages"][0]["content"][0]["text"]:
        if "A person name is included." in prompt.to_dict()["messages"][0]["content"][0]["text"]:
            return "TRUE"
        return "Michael Jordan"
    elif "What is 3 * 5? return just the answer and nothing else." in prompt.to_dict()["messages"][0]["content"][0]["text"]:
        return "15"
    else:
        return "FALSE"

class TestSmartLogicHelper(unittest.TestCase):
    def setUp(self):
        context = AgentContext(agent_id="test_agent")
        self.helper = SmartLogicHelper(context)

        lm = MagicMock()
        lm.generate = mock_generate
        self.helper.set_default_lm(lm)

    def test_smart_extract(self):
        paragraph = "Michael Jordan is a retired professional basketball player. He is widely regarded as one of the greatest basketball players of all time."
        self.assertEqual(self.helper.smart_extract(paragraph, "person name"), "Michael Jordan")
    
    def test_smart_judge(self):
        paragraph = "Michael Jordan is a retired professional basketball player. He is widely regarded as one of the greatest basketball players of all time."
        condition = "A person name is included."
        self.assertEqual(self.helper.smart_judge(paragraph, condition), True)
    
    def test_prompt(self):
        prompt = "What is 3 * 5? return just the answer and nothing else."
        result = self.helper.prompt(prompt)
        self.assertEqual(result, "15")
