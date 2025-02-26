import importlib
import os
import shutil
import sys
import uuid

from chorus.config.params import Params
from chorus.workspace.workspace import Workspace

TMP_CODE_PATH = "/tmp/custom_agents_code"
sys.path.append(TMP_CODE_PATH)


def load_workspace(workspace_folder):
    def_path = f"{workspace_folder}/ws.jsonnet"
    if not os.path.exists(def_path):
        ws = None
    else:
        solution_path = f"{workspace_folder}/agents.py"
        if os.path.exists(solution_path):
            if not os.path.exists(TMP_CODE_PATH):
                os.makedirs(TMP_CODE_PATH)
            random_filename = "agent_" + str(uuid.uuid4())[:6] + ".py"
            shutil.copyfile(solution_path, f"{TMP_CODE_PATH}/{random_filename}")
            spec = importlib.util.spec_from_file_location(
                random_filename.replace(".py", ""), f"{TMP_CODE_PATH}/{random_filename}"
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules[random_filename.replace(".py", "")] = mod
            spec.loader.exec_module(mod)
        ws = Workspace.from_params(Params.from_file(def_path))

    return ws
