import unittest

from chorus.data.context import AgentContext
from chorus.helpers.smart_logic import SmartLogicHelper


class TestSmartLogicHelper(unittest.TestCase):

    def test_smart_extract(self):
        context = AgentContext(agent_id="test_agent")
        helper = SmartLogicHelper(context)
        paragraph = "Michael Jordan is a retired professional basketball player. He is widely regarded as one of the greatest basketball players of all time."
        self.assertEqual(helper.smart_extract(paragraph, "person name"), "Michael Jordan")
    
    def test_smart_judge(self):
        context = AgentContext(agent_id="test_agent")
        helper = SmartLogicHelper(context)
        paragraph = "Michael Jordan is a retired professional basketball player. He is widely regarded as one of the greatest basketball players of all time."
        condition = "A person name is included."
        self.assertEqual(helper.smart_judge(paragraph, condition), True)
    
    def test_prompt(self):
        context = AgentContext(agent_id="test_agent")
        helper = SmartLogicHelper(context)
        prompt = "What is 3 * 5? return just the answer and nothing else."
        result = helper.prompt(prompt)
        self.assertEqual(result, "15")
