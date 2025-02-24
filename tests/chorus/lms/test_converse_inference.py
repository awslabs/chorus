import pytest
from chorus.data import StructuredPrompt
from chorus.lms.bedrock_converse import BedrockConverseAPIClient

def test_bedrock_converse_generate():
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