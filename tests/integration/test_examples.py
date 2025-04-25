import unittest
import importlib.util
from unittest.mock import patch, MagicMock
from chorus.data import SimpleExecutableTool
from chorus.data import ToolSchema

class mock_os():
    def getenv(self, key):
        return "mock_api_key"

class mock_WebSearchTool(SimpleExecutableTool):
    def __init__(self):
        from chorus.toolbox.web_search import schema
        super().__init__(ToolSchema.model_validate(schema))
    def search(self, query):
        return "No results found."

class TestExamples(unittest.TestCase):
    def _import_example(self, example_path):
        print(f"Importing example {example_path} for testing")

        # Import the module dynamically
        spec = importlib.util.spec_from_file_location(
            "example_module",
            f"examples/python/{example_path}"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, 'main'):
            raise ValueError(f"Example {example_path} does not have a main function")

        return module
    
    def test_agent_triggers(self):
        module = self._import_example("agent_triggers.py")
        with patch.object(module, "argparse") as mock_argparse, \
            patch('chorus.toolbox.serper_search.os', wraps=mock_os), \
            patch('chorus.core.runner.Chorus.wait_for_response') as mock_wait_for_response, \
            patch('chorus.core.runner.VisualDebugger') as mock_VisualDebugger:
            mock_argparse.ArgumentParser.return_value = MagicMock()
            mock_argparse.ArgumentParser.return_value.parse_args.return_value = MagicMock()
            mock_wait_for_response.return_value = None
            module.main()
    
    def test_basic_single_agent(self):
       module = self._import_example("basic_single_agent.py")
       module.main()
    
    # def test_centralized_financial_risk_report_generation(self):
    #     """TODO: fix custom agent class pickle issue"""
    #     class mock_RemotePDFReaderTool():
    #         def read(self, url):
    #             return "No results found."
    #     module = self._import_example("centralized_financial_risk_report_generation.py")
    #     with patch('chorus.toolbox.serper_search.os', wraps=mock_os), \
    #         patch('chorus.toolbox.serper_search.requests') as mock_requests, \
    #         patch('chorus.core.runner.Chorus.wait_for_response') as mock_wait_for_response, \
    #         patch.object(module, "RemotePDFReaderTool", wraps=mock_RemotePDFReaderTool), \
    #         patch('chorus.core.runner.VisualDebugger') as mock_VisualDebugger:
    #         mock_requests.request.return_value = MagicMock()
    #         mock_requests.request.return_value.text = "{}"
    #         module.main()
    
    def test_collaboration_centralized_conversational_routing(self):
        module = self._import_example("collaboration_centralized_conversational_routing.py")
        module.main()

    def test_decentralized_business_debate(self):
        module = self._import_example("decentralized_business_debate.py")
        with patch('chorus.core.runner.Chorus.wait_for_response') as mock_wait_for_response, \
            patch('chorus.core.runner.VisualDebugger') as mock_VisualDebugger:
            module.main()
    
    def test_decentralized_collaboration(self):
        module = self._import_example("decentralized_collaboration.py")
        with patch('chorus.core.runner.Chorus.wait_for_response') as mock_wait_for_response, \
            patch('chorus.core.runner.VisualDebugger') as mock_VisualDebugger:
            module.main()

    def test_decentralized_news_investigation(self):
        module = self._import_example("decentralized_news_investigation.py")
        with patch('chorus.toolbox.serper_search.os', wraps=mock_os), \
            patch('chorus.core.runner.Chorus.wait_for_response') as mock_wait_for_response, \
            patch('chorus.core.runner.VisualDebugger') as mock_VisualDebugger:
            module.main()
    
    def test_hello_world(self):
        module = self._import_example("hello_world.py")
        with patch('chorus.helpers.communication.CommunicationHelper.wait') as mock_wait, \
            patch.object(module, "DuckDuckGoWebSearchTool", wraps=mock_WebSearchTool):
            module.main()

    # def test_langchain_agent(self):
    #     """TODO: fix custom agent class pickle issue"""
    #     module = self._import_example("langchain_agent.py")
    #     with patch('chorus.core.runner.Chorus.wait_for_response') as mock_wait_for_response:
    #         module.main()
    
    # def test_llamaindex_agent_bedrock(self):
    #     """TODO: fix custom agent class pickle issue"""
    #     module = self._import_example("llamaindex_agent_bedrock.py")
    #     with patch('chorus.core.runner.Chorus.wait_for_response') as mock_wait_for_response:
    #         module.main()
    
    def test_multi_agent_workflow(self):
        module = self._import_example("multi_agent_workflow.py")
        with patch('chorus.helpers.communication.CommunicationHelper.wait') as mock_wait, \
            patch.object(module, "DuckDuckGoWebSearchTool", wraps=mock_WebSearchTool):
            module.main()
    
    def test_start_chorus_in_a_thread(self):
        module = self._import_example("start_chorus_in_a_thread.py")
        with patch('chorus.helpers.communication.CommunicationHelper.wait') as mock_wait:
            module.main()
    
    def test_team_async_tool_calling(self):
        module = self._import_example("team_async_tool_calling.py")
        module.main()
    
    # def test_use_visual_debugger(self):
    #     """TODO: fix custom agent class pickle issue"""
    #     module = self._import_example("use_visual_debugger.py")
    #     with patch('chorus.core.runner.Chorus.wait_for_response') as mock_wait_for_response, \
    #         patch('chorus.core.runner.VisualDebugger') as mock_VisualDebugger:
    #         module.main()