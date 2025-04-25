from unittest.mock import patch, MagicMock
from chorus.toolbox import ArxivRetrieverTool
import dotenv

@patch("chorus.toolbox.arxiv_tool.arxiv")
def test_arxiv_retriever_tool(mock_arxiv):
    mock_arxiv.Client.return_value = MagicMock()
    mock_arxiv.Client.return_value.results.return_value = [
        MagicMock(
            entry_id='foobar',
            title='Test Title',
            summary='Test Summary',
            authors=[MagicMock(name='Test Author')],
        )
    ]

    # Load environment variables
    dotenv.load_dotenv()
    
    # Initialize tool
    tool = ArxivRetrieverTool()
    
    # Perform search
    results = tool.search('speculative decoding')
    
    # Basic assertions
    assert results is not None
    assert len(results) > 0
