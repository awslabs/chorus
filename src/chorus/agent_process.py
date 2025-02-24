
import json
import os
import signal
import sys
import time
from typing import Dict, Optional

from chorus.agents import Agent
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.dialog import Message

class AgentProcess:
    """A process that runs a single agent and communicates with the Chorus runner."""
    
    def __init__(
        self,
        agent_id: str,
        data_file: str,
        read_pipe: str,
        write_pipe: str,
        debug: bool = False
    ):
        self.agent_id = agent_id
        self.data_file = data_file
        self.read_pipe = read_pipe
        self.write_pipe = write_pipe
        self.debug = debug
        
        # Load initial agent data
        with open(data_file, 'r') as f:
            self.agent_data = json.load(f)
            
        # Parse context and state from JSON
        context_dict = json.loads(self.agent_data["context"])
        
        # Initialize a new message service for this process
        from chorus.environment.communication import MessageService
        message_service = MessageService()
        if 'message_service' in context_dict:
            messages = context_dict['message_service'].get('message_history', [])
            message_service.message_history = messages
        context_dict['message_service'] = message_service
        
        # Remove fields that will be reinitialized
        context_dict.pop('status_manager', None)
        
        # Reconstruct agent tools
        if 'tools' in context_dict:
            from chorus.data.tool import AgentAsATool
            tools = []
            for tool in context_dict['tools']:
                if isinstance(tool, dict) and tool.get('type') == 'agent_as_tool':
                    tools.append(AgentAsATool(
                        name=tool['name'],
                        description=tool['description'],
                        agent_id=tool['agent_id']
                    ))
                else:
                    tools.append(tool)
            context_dict['tools'] = tools
        
        # Create the context
        self.context = AgentContext.model_validate(context_dict)
        self.state = AgentState.model_validate_json(self.agent_data["state"])
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_termination)
        signal.signal(signal.SIGINT, self.handle_termination)
        
        self._stopping = False
    
    def handle_termination(self, signum, frame):
        """Handle termination signals by cleaning up and saving state."""
        self._stopping = True
        self.save_state()
        sys.exit(0)
    
    def save_state(self):
        """Save the current agent state and context to the data file."""
        agent_data = {
            "agent_id": self.agent_id,
            "context": self.context.model_dump_json(),
            "state": self.state.model_dump_json()
        }
        with open(self.data_file, 'w') as f:
            json.dump(agent_data, f)
    
    def read_message(self) -> Optional[Dict]:
        """Read a message from the read pipe."""
        try:
            with open(self.read_pipe, 'r') as f:
                data = f.read()
                if data:
                    return json.loads(data)
        except Exception as e:
            if self.debug:
                print(f"Error reading message: {e}", file=sys.stderr)
        return None
    
    def write_message(self, message: Dict):
        """Write a message to the write pipe."""
        try:
            with open(self.write_pipe, 'w') as f:
                json.dump(message, f)
                f.flush()
        except Exception as e:
            if self.debug:
                print(f"Error writing message: {e}", file=sys.stderr)
    
    def run(self):
        """Main agent process loop."""
        while not self._stopping:
            # Read any incoming messages
            message_data = self.read_message()
            if message_data:
                try:
                    message = Message.model_validate(message_data)
                    # Update agent state based on message
                    self.state = self.context.agent.iterate(self.context, self.state, message)
                    # Save updated state
                    self.save_state()
                    # Sync messages back to main process
                    self.write_message({
                        "type": "state_update",
                        "agent_id": self.agent_id,
                        "context": self.context.model_dump(),
                        "state": self.state.model_dump()
                    })
                except Exception as e:
                    if self.debug:
                        print(f"Error processing message: {e}", file=sys.stderr)
                    self.write_message({
                        "type": "error",
                        "agent_id": self.agent_id,
                        "error": str(e)
                    })
            
            # Small sleep to prevent busy waiting
            time.sleep(0.1)

def main():
    parser = argparse.ArgumentParser(description="Run an Chorus agent in a separate process")
    parser.add_argument("--agent-id", required=True, help="Unique identifier for the agent")
    parser.add_argument("--data-file", required=True, help="Path to the agent data file")
    parser.add_argument("--read-pipe", required=True, help="Path to the read pipe")
    parser.add_argument("--write-pipe", required=True, help="Path to the write pipe")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    agent_process = AgentProcess(
        agent_id=args.agent_id,
        data_file=args.data_file,
        read_pipe=args.read_pipe,
        write_pipe=args.write_pipe,
        debug=args.debug
    )
    
    try:
        agent_process.run()
    except Exception as e:
        print(f"Agent process error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 