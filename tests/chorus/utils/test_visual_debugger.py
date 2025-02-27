import os
import json
import tempfile
from chorus.util.visual_debugger import VisualDebugger
import requests
import time
from unittest.mock import patch

def test_visual_debugger_initialization():
    """Test basic initialization of visual debugger."""
    debugger = VisualDebugger(port=5050)
    assert debugger.port == 5050
    assert isinstance(debugger.log_files, dict)
    assert debugger.server_thread is None

def test_add_agent_log():
    """Test adding agent log files."""
    debugger = VisualDebugger()
    debugger.add_agent_log("agent1", "/path/to/log1")
    debugger.add_agent_log("agent2", "/path/to/log2")
    
    assert "agent1" in debugger.log_files
    assert debugger.log_files["agent1"] == "/path/to/log1"
    assert "agent2" in debugger.log_files
    assert debugger.log_files["agent2"] == "/path/to/log2"

def test_get_agent_messages():
    """Test parsing and filtering agent messages."""
    debugger = VisualDebugger()
    
    # Create a temporary messages log file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        # Write some test messages
        messages = [
            {"message_id": "1", "source": "agent1", "destination": "agent2", "content": "Hello"},
            {"message_id": "2", "source": "agent2", "destination": "agent1", "content": "Hi back"},
            {"message_id": "3", "source": "agent3", "destination": "agent1", "content": "Hey"},
            {"message_id": "4", "source": "agent1", "destination": "agent3", "content": "Hello there"}
        ]
        for msg in messages:
            f.write(json.dumps(msg) + '\n')
    
    try:
        # Test messages for agent1
        agent1_messages = debugger._get_agent_messages(f.name, "agent1")
        assert len(agent1_messages) == 4  # agent1 is involved in all messages
        
        # Test messages for agent2
        agent2_messages = debugger._get_agent_messages(f.name, "agent2")
        assert len(agent2_messages) == 2  # agent2 is involved in 2 messages
        
        # Verify message content
        assert any(msg["content"] == "Hello" for msg in agent1_messages)
        assert any(msg["content"] == "Hi back" for msg in agent2_messages)
        
    finally:
        # Clean up
        os.unlink(f.name)

def test_visual_debugger_server():
    """Test that the visual debugger server starts and serves content."""
    debugger = VisualDebugger(port=5555)
    
    # Create a temporary log file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test log content")
        log_path = f.name
    
    try:
        # Add test agent
        debugger.add_agent_log("test_agent", log_path)
        
        # Start server with mocked browser opening
        with patch('webbrowser.open'):
            debugger.start()
            
            # Give the server a moment to start
            time.sleep(1)
            
            # Test that server is running and responding
            response = requests.get('http://localhost:5555')
            assert response.status_code == 200
            
            # Check content
            content = response.text
            assert "Chorus Visual Debugger" in content
            assert "test_agent" in content
            assert "Test log content" in content
            
    finally:
        # Clean up
        os.unlink(log_path)

def test_invalid_message_handling():
    """Test handling of invalid message formats in log file."""
    debugger = VisualDebugger()
    
    # Create a temporary messages log file with some invalid content
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        # Write test messages with various formats
        f.write('{"valid": "json", "but": "wrong format"}\n')  # Valid JSON but wrong message format
        f.write('invalid json content\n')  # Invalid JSON
        f.write('{"source": "agent1", "destination": "agent2"}\n')  # Missing required fields
        f.write('{"message_id": "1", "source": "agent1", "destination": "agent2", "content": "Valid"}\n')  # Valid message for agent1
        f.write('{"message_id": "2", "source": "agent3", "destination": "agent4", "content": "Not for agent1"}\n')  # Valid but not for agent1
    
    try:
        # Test messages for agent1
        messages = debugger._get_agent_messages(f.name, "agent1")
        assert len(messages) == 1  # Only the valid message for agent1 should be included
        assert messages[0]["content"] == "Valid"
        assert messages[0]["source"] == "agent1"
        
        # Test messages for agent3
        messages = debugger._get_agent_messages(f.name, "agent3")
        assert len(messages) == 1  # Only the valid message for agent3 should be included
        assert messages[0]["content"] == "Not for agent1"
        assert messages[0]["source"] == "agent3"
        
    finally:
        # Clean up
        os.unlink(f.name)

def test_nonexistent_log_file():
    """Test handling of non-existent log files."""
    debugger = VisualDebugger()
    
    # Test with non-existent file
    messages = debugger._get_agent_messages("/nonexistent/file.log", "agent1")
    assert messages == []  # Should return empty list for non-existent files 