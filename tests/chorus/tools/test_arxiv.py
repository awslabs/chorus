import pytest
from chorus.toolbox import ArxivRetrieverTool
import dotenv

def test_arxiv_retriever_tool():
    # Load environment variables
    dotenv.load_dotenv()
    
    # Initialize tool
    tool = ArxivRetrieverTool()
    
    # Perform search
    results = tool.search('speculative decoding')
    
    # Basic assertions
    assert results is not None
    assert len(results) > 0
