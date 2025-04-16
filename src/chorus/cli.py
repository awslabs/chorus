import logging
import os.path
import shutil
import sys
from argparse import ArgumentParser

from dotenv import load_dotenv

if "--debug" in sys.argv:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler("env/debug.log")],
    )
else:
    logging.basicConfig(level=logging.ERROR)

from chorus.data import Message
from chorus.workspace.workspace_util import load_workspace
from chorus.core.runner import Chorus
from chorus.workspace.stop_conditions import NoActivityStopper

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DEFAULT_WORKSPACE_ROOT = f"."
EXAMPLE_WORKSPACE_ROOT = f"{ROOT}/examples/workspaces"
HELLO_WORLD_WORKSPACE = f"{EXAMPLE_WORKSPACE_ROOT}/hello_world"


def migrate_jsonnet_to_yaml(workspace_root):
    """
    Help users migrate from jsonnet to YAML.
    
    Args:
        workspace_root (str): Root directory for workspaces
    """
    print("Beginning migration from jsonnet to YAML...")
    
    # Find all jsonnet files in workspaces
    jsonnet_files = []
    for root, dirs, files in os.walk(workspace_root):
        for file in files:
            if file.endswith(".jsonnet"):
                jsonnet_files.append(os.path.join(root, file))
    
    if not jsonnet_files:
        print("No jsonnet files found. No migration needed.")
        return
    
    print(f"Found {len(jsonnet_files)} jsonnet files that need to be converted to YAML.")
    print("""
MIGRATION INSTRUCTIONS: Jsonnet to YAML
---------------------------------------

Chorus has migrated from using jsonnet to YAML for workspace configuration.
To convert your existing jsonnet files:

1. Install the jsonnet package if not already installed:
   pip install jsonnet

2. For each jsonnet file:
   a. Evaluate the jsonnet file to JSON:
      jsonnet path/to/workspace/ws.jsonnet > temp.json
      
   b. Convert the JSON to YAML:
      python -c "import yaml, json; print(yaml.dump(json.load(open('temp.json')), default_flow_style=False, sort_keys=False))" > path/to/workspace/ws.yaml
      
   c. Remove the temporary JSON file:
      rm temp.json

3. Update your workflow to use ws.yaml instead of ws.jsonnet
""")
    
    # Try automated conversion if jsonnet is installed
    try:
        choice = input("\nWould you like to attempt automated conversion? (requires jsonnet package) [y/N]: ")
        if choice.lower() == 'y':
            print("\nAttempting automated conversion...")
            try:
                # Import jsonnet only if user wants automated conversion
                from _jsonnet import evaluate_file
                import yaml
                import json
                
                for file in jsonnet_files:
                    try:
                        # Convert jsonnet to JSON
                        json_str = evaluate_file(file)
                        json_data = json.loads(json_str)
                        
                        # Convert JSON to YAML
                        yaml_file = file.replace(".jsonnet", ".yaml")
                        with open(yaml_file, "w") as f:
                            yaml.dump(json_data, f, default_flow_style=False, sort_keys=False)
                        
                        print(f"Converted {file} to {yaml_file}")
                    except Exception as e:
                        print(f"Error converting {file}: {e}")
                
                print("\nConversion completed. Please verify the YAML files before removing the original jsonnet files.")
            except ImportError:
                print("jsonnet package not installed. Please follow the manual conversion instructions.")
    except KeyboardInterrupt:
        print("\nCanceled.")


if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument(
        "command", help="Command to execute", choices=["create", "run", "check", "deploy", "migrate"]
    )
    ap.add_argument("-r", "--root", default=DEFAULT_WORKSPACE_ROOT, help="Root directory for workspaces")
    ap.add_argument("-w", "--workspace", help="Name of workspace to create or use")
    ap.add_argument("-i", "--input", help="Initial message to default agent", default=None)
    ap.add_argument("--debug", action="store_true", help="Enable debug mode")
    ap.add_argument("--visual", action="store_true", help="Enable visual debugger")
    ap.add_argument("--visual-port", type=int, default=5000, help="Port for visual debugger (default: 5000)")
    args = ap.parse_args()

    if args.command == "migrate":
        migrate_jsonnet_to_yaml(args.root)
    else:
        # All other commands require a workspace
        if not args.workspace:
            print("Error: Workspace name is required for this command")
            ap.print_help()
            sys.exit(1)
            
        ws_name = args.workspace
        ws_folder = os.path.join(args.root, ws_name)

        if args.command == "create":
            if os.path.exists(ws_folder):
                print(f"Workspace {ws_name} already exists in {ws_folder}.")
            else:
                shutil.copytree(HELLO_WORLD_WORKSPACE, ws_folder)
                print(f"Created workspace {ws_name} in [{ws_folder}]")
            print()
            print(f"Configure your workspace by:")
            print(f"vim {ws_folder}/ws.yaml")
            print()
            print(f"Run your workspace with:")
            print(f"python -m chorus.cli run -w {ws_name}")

        elif args.command == "run":
            if not os.path.exists(ws_folder):
                print(f"Workspace {ws_name} does not exist in {ws_folder}.")
                exit(1)
            print(f">>> Running workspace <{ws_name}> <<<")
            ws = load_workspace(ws_folder)
            stop_conditions = ws.stop_conditions if ws.stop_conditions else []
            stop_conditions.append(NoActivityStopper(no_activity_time_threshold=5))
            runner = Chorus(
                agents=ws.agents, 
                teams=ws.teams, 
                stop_conditions=stop_conditions,
                debug=args.debug,
                visual=args.visual,
                visual_port=args.visual_port
            )
            for message in ws.start_messages:
                env = runner.get_environment()
                if env is not None:
                    env.send_message(
                        Message(
                            source=message.get("source", None),
                            destination=message.get("destination", None),
                            channel=message.get("channel", None),
                            content=message.get("content", None),
                        )
                    )

            if ws.main_channel is None:
                raise ValueError("No default channel specified in workspace.")
            n_round = 0
            while True:
                n_round += 1
                if n_round == 1 and args.input is not None:
                    human_input = args.input
                else:
                    print("===========================================")
                    print("(Press enter a messages, or press Enter / type 'exit' to quit.)")
                    human_input = input(f"Human -> {ws.main_channel}: ")
                if not human_input.strip() or human_input.strip().lower() == "exit":
                    break
                env = runner.get_environment()
                if env is not None:
                    env.send_message(
                        source="human",
                        destination=ws.main_channel,
                        message=Message(content=human_input),
                    )
                runner.run()
        else:
            print(f"{args.command} is not a valid command or not implemented yet.")
