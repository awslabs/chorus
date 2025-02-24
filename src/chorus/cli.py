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
from chorus.util.workspace_util import load_workspace
from chorus.core.runner import Chorus
from chorus.workspace.stop_conditions import NoActivityStopper

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DEFAULT_WORKSPACE_ROOT = f"."
EXAMPLE_WORKSPACE_ROOT = f"{ROOT}/example_workspaces"
HELLO_WORLD_WORKSPACE = f"{EXAMPLE_WORKSPACE_ROOT}/hello_world"


if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument(
        "command", help="Command to execute", choices=["create", "run", "check", "deploy"]
    )
    ap.add_argument("-r", "--root", default=DEFAULT_WORKSPACE_ROOT, help="Root directory for workspaces")
    ap.add_argument("-w", "--workspace", help="Name of workspace to create or use", required=True)
    ap.add_argument("-i", "--input", help="Initial message to default agent", default=None)
    ap.add_argument("--debug", action="store_true", help="Enable debug mode")
    ap.add_argument("--visual", action="store_true", help="Enable visual debugger")
    ap.add_argument("--visual-port", type=int, default=5000, help="Port for visual debugger (default: 5000)")
    args = ap.parse_args()

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
        print(f"vim {ws_folder}/ws.jsonnet")
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
            runner.get_environment().send_message(
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
            runner.get_environment().send_message(
                source="human",
                destination=ws.main_channel,
                message=Message(content=human_input),
            )
            runner.run()
    else:
        print(f"{args.command} is not a valid command or not implemented yet.")
