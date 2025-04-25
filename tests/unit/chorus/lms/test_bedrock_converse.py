from unittest.mock import patch, MagicMock
from chorus.data import StructuredPrompt
from chorus.lms.bedrock_converse import BedrockConverseAPIClient

@patch('chorus.lms.bedrock_converse.boto3')
def test_bedrock_converse_generate(mock_boto3):
    mock_boto3.Session.return_value = MagicMock()
    mock_boto3.Session.return_value.client.return_value = MagicMock()
    mock_boto3.Session.return_value.client.return_value.converse.return_value = {
        "output": "Hello, world!"
    }

    # Initialize client
    client = BedrockConverseAPIClient("anthropic.claude-3-sonnet-20240229-v1:0")
    client.set_default_options({
        "maxTokens": 128
    })

    # Test prompt
    prompt = "What is a language model?"
    
    # Create structured prompt
    structured_prompt = StructuredPrompt.from_dict({
        "messages": [
            {
                "role": "user", 
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    })

    # Generate response
    response = client.generate(prompt=structured_prompt)
    
    # Basic assertions
    assert response is not None