import multiprocessing
import os
import sys
import threading
import time
from multiprocessing import Process
from os import getpid
from typing import Dict
from typing import List
from typing import Optional
import uuid
import contextlib
from io import StringIO

from chorus.agents import Agent
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.agent_status import AgentStatus
from chorus.data.channel import Channel
from chorus.data.team_info import TeamInfo
from chorus.environment.global_context import ChorusGlobalContext
from chorus.core.state import RunnerState
from chorus.teams import Team
from chorus.workspace.stop_conditions import MultiAgentStopCondition
from chorus.util.visual_debugger import VisualDebugger

import signal

MAX_INSTNACE_LIMIT = 500

class TeeIO:
    def __init__(self, file_path):
        self.file = open(file_path, 'a', encoding='utf-8')
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        
    def write(self, data):
        self.file.write(data)
        self.file.flush()
        if self.stdout:
            self.stdout.write(data)
            self.stdout.flush()
            
    def flush(self):
        self.file.flush()
        if self.stdout:
            self.stdout.flush()
            
    def close(self):
        self.file.close()

class Chorus(object):
    """Chorus runner that manages and coordinate multiple agents and teams in an orchestrated environment.

    This class serves as the main runner for coordinating agents and teams,
    managing their communication channels, and controlling their execution flow.

    Args:
        agents: List of individual agents to be managed by the chorus.
        teams: List of teams (groups of agents) to be managed by the chorus.
        channels: List of communication channels for agents/teams to interact.
        global_context: Global context object containing shared state and resources.
        simulator_state: State object tracking the status of all agents/teams.
        max_idle_time: Maximum time in seconds to wait while system is idle before stopping.
        tick_interval: Time in seconds between system update ticks.
        stop_conditions: List of conditions that will trigger the chorus to stop.
        debug: Whether to run in debug mode with additional logging.
        visual: Whether to enable visual debugging.
        visual_port: Port for the visual debugger.

    Raises:
        ValueError: If neither agents nor teams are specified, or if the total number
            of agents and teams exceeds MAX_INSTNACE_LIMIT.
    """

    def __init__(
        self,
        agents: Optional[List[Agent]] = None,
        teams: Optional[List[Team]] = None,
        channels: Optional[List[Channel]] = None,
        global_context: ChorusGlobalContext = None,
        simulator_state: RunnerState = None,
        max_idle_time: int = 300,
        tick_interval: int = 1,
        stop_conditions: Optional[List[MultiAgentStopCondition]] = None,
        debug: bool = False,
        visual: bool = False,
        visual_port: int = 5000,
    ):
        """Initialize the runner with configuration.

        Args:
            agents (Optional[List[Agent]]): List of agents to be managed.
            teams (Optional[List[Team]]): List of teams to be managed.
            channels (Optional[List[Channel]]): List of channels to be managed.
            global_context (ChorusGlobalContext): Global context for the chorus.
            simulator_state (RunnerState): State of the simulator.
            max_idle_time (int): Maximum idle time before stopping.
            tick_interval (int): Interval between ticks.
            stop_conditions (Optional[List[MultiAgentStopCondition]]): List of stop conditions.
            debug (bool): Debug mode flag.
            visual (bool): Visual debugging flag.
            visual_port (int): Port for the visual debugger.
        """
        if not agents and not teams:
            raise ValueError("Either agents or teams need to be specified for launching the Chorus runner.")
        self._max_idle_time = max_idle_time
        self._tick_interval = tick_interval
        self._agents = agents if agents is not None else []
        self._teams = teams if teams is not None else []
        if len(self._agents) + len(self._teams) > MAX_INSTNACE_LIMIT:
            raise ValueError(f"The number of agents and teams exceeds the maximum limit: {MAX_INSTNACE_LIMIT}")
        self._agent_map = {}
        self._agent_team_map = {}
        self._global_context = global_context
        self._proc_manager = multiprocessing.Manager()
        self._is_busy = False
        self._last_busy_timestamp = int(time.time())
        self._debug = debug
        self._visual = visual
        self._visual_debugger = None
        self._chorus_thread = None
        self._logged_message_ids = set()  # Track which messages have been logged
        if self._visual:
            self._visual_debugger = VisualDebugger(port=visual_port)
            # Register teams and channels with the visual debugger
            if self._teams:
                for team in self._teams:
                    self._visual_debugger.add_team(team)
            if channels:
                for channel in channels:
                    self._visual_debugger.add_channel(channel)
        if self._global_context is None:
            self._global_context = ChorusGlobalContext(self._proc_manager)
        if channels is not None:
            for channel in channels:
                self._global_context.register_channel(channel)
        self._simulator_state = simulator_state
        if self._simulator_state is None:
            self._simulator_state = RunnerState()
        self._stop_conditions = stop_conditions
        if self._stop_conditions is None:
            self._stop_conditions = []
        for stopper in self._stop_conditions:
            stopper.set_runner(self)
        # Initialize agent contexts and states
        if self._agents:
            for agent in self._agents:
                self.spawn_agent(agent)
        if self._teams:
            for team in self._teams:
                self.spawn_agent(team)
                team_info = team.get_team_info()
                agent_ids = []
                for agent in team.get_agents():
                    agent_id = self.spawn_agent(agent, team_info=team_info)
                    agent_ids.append(agent_id)
                team_info.agent_ids = agent_ids
        self.register_signal_handler()
        self.alive_processes = []
        self._stopping = False
        self._global_run_uuid = str(uuid.uuid4())[:8]

    def spawn_agent(self, agent: Agent, team_info: Optional[TeamInfo] = None) -> str:
        context = agent.init_context()
        context.artifacts = self._proc_manager.dict(**context.artifacts)
        if team_info is not None:
            context.team_info = team_info
        state = agent.init_state()
        self._global_context.register_agent_context(context)
        self._simulator_state.update_agent_state(context.agent_id, state)
        self._agent_map[context.agent_id] = agent
        if team_info is not None:
            self._agent_team_map[context.agent_id] = team_info.get_identifier()
        return context.agent_id

    def run(self):
        """Execute the main running loop for agent collaboration and block the thread.

        Manages the lifecycle of agents, coordinates their interactions, and handles
        any errors or exceptions that occur during execution.

        Returns:
            Dict: Results of the execution including agent outputs and final state.

        Raises:
            RunnerError: If there is an error during execution.
        """
        self._is_busy = True
        self.alive_processes = []
        busy_agents_set = set()
        return_dict = self._proc_manager.dict()
        self._last_busy_timestamp = int(time.time())

        # Start visual debugger if enabled
        if self._visual and self._visual_debugger:
            self._visual_debugger.start()
            # Register all agent log files and states
            for agent_id in self._agent_map.keys():
                log_file = f"/tmp/chorus_agent_instance_log_{self._global_run_uuid}_{agent_id}.log"
                self._visual_debugger.add_agent_log(agent_id, log_file)
                # Register agent states
                state = self._simulator_state.get_agent_state(agent_id)
                if state:
                    self._visual_debugger.register_state(agent_id, state)

        try:
            while True:
                triggered_agent_count = 0
                # Maintain processes
                new_alive_processes = []
                for proc, agent_id in self.alive_processes:
                    if not proc.is_alive():
                        if proc.pid not in return_dict:
                            # Error is detected, clean up all processes and exit
                            try:
                                terminal_size = os.get_terminal_size().columns
                            except OSError:
                                terminal_size = 80
                            print("\033[1;41m" + "=" * terminal_size + "\033[0m")
                            print(f"\033[1;41m Chorus Agent Crashed: {agent_id} \033[0m")
                            print("\033[1;41m" + "=" * terminal_size + "\033[0m")
                            for proc, _ in self.alive_processes:
                                if proc.is_alive():
                                    proc.terminate()
                            if self._visual:
                                print(f"\nVisual debugger is still running at http://localhost:{self._visual_debugger.port}")
                                print("Check the agent logs in the browser to see what went wrong")
                                print("Press Enter to exit...")
                                input()
                            raise SystemError(f"Chorus agent process crashed: {agent_id}")
                        context, state = return_dict[proc.pid]
                        del return_dict[proc.pid]
                        self._global_context.update_agent_context(agent_id, context)
                        self._simulator_state.update_agent_state(agent_id, state)
                        if self._visual_debugger:
                            self._visual_debugger.register_state(agent_id, state)
                        busy_agents_set.remove(agent_id)
                    else:
                        self._global_context.sync_agent_messages(agent_id)
                        new_alive_processes.append((proc, agent_id))
                self.alive_processes = new_alive_processes
                # Update the latest message pool into a log file in the case of visual debugging
                if self._visual and self._visual_debugger:
                    # Dump global messages to log file
                    messages_log_path = f"/tmp/chorus_agent_instance_log_{self._global_run_uuid}_messages.jsonl"
                    new_messages = []
                    for msg in self._global_context.message_service.fetch_all_messages():
                        if msg.message_id not in self._logged_message_ids:
                            new_messages.append(msg)
                            self._logged_message_ids.add(msg.message_id)
                    
                    if new_messages:  # Only write if there are new messages
                        with open(messages_log_path, 'a') as f:
                            for msg in new_messages:
                                f.write(msg.model_dump_json() + '\n')
                    
                    # Make sure the visual debugger knows about the messages log file
                    self._visual_debugger.add_agent_log('messages', messages_log_path)
                # Run agents
                for agent_id, agent in self._agent_map.items():
                    if agent_id in busy_agents_set:
                        continue
                    context = self._global_context.get_agent_context(agent_id)
                    state = self._simulator_state.get_agent_state(agent_id)
                    if self._debug:
                        self.iterate_agent(self._global_run_uuid, agent, context, state, return_dict)
                        proc = Process(target=time.time)
                        proc.start()
                    else:
                        proc = Process(
                            target=Chorus.iterate_agent,
                            args=(self._global_run_uuid, agent, context, state, return_dict),
                        )
                        proc.start()
                    self.alive_processes.append((proc, agent_id))
                    busy_agents_set.add(agent_id)
                    triggered_agent_count += 1
                self.dump_environment_state()
                if not triggered_agent_count:
                    time.sleep(self._tick_interval)
                # Ending
                ending = False
                if self._stopping:
                    print("Chorus is stopping...")
                    break
                for stopper in self._stop_conditions:
                    if stopper.stop():
                        print(f"Simulator stopped due to {str(stopper)}")
                        ending = True
                        break
                if ending:
                    break
        finally:
            # Terminate processes
            for proc, _ in self.alive_processes:
                if proc.is_alive():
                    proc.terminate()
            self._is_busy = False

    def is_busy(self):
        return self._is_busy

    @staticmethod
    def iterate_agent(global_run_uuid: str, agent: Agent, context: AgentContext, state: AgentState, return_dict: Dict):
        log_path = f"/tmp/chorus_agent_instance_log_{global_run_uuid}_{context.agent_id}.log"
        tee = TeeIO(log_path)
        with contextlib.redirect_stdout(tee), contextlib.redirect_stderr(tee):
            try:
                new_state = agent.iterate(context, state)
                return_dict[getpid()] = (context, new_state)
            except Exception as e:
                import traceback
                error_msg = f"\n{'='*60}\nERROR: Agent {context.agent_id} crashed with exception:\n"
                error_msg += f"\nException Type: {type(e).__name__}"
                error_msg += f"\nException Message: {str(e)}"
                error_msg += f"\n\nFull Traceback:\n{traceback.format_exc()}"
                error_msg += f"\n{'='*60}\n"
                with open(log_path, "a") as f:
                    f.write(error_msg)
                    f.flush()
                raise  # Re-raise the exception after logging
            finally:
                tee.close()

    def get_environment(self) -> ChorusGlobalContext:
        return self._global_context
    
    def get_global_context(self) -> ChorusGlobalContext:
        return self._global_context
    
    def get_global_state(self) -> RunnerState:
        return self._simulator_state
    
    def get_agent_context(self, agent_id: str) -> Optional[AgentContext]:
        return self._global_context.get_agent_context(agent_id)
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        return self._simulator_state.get_agent_state(agent_id)

    def dump_environment_state(self):
        pass

    def get_agents_status(self) -> Dict[str, AgentStatus]:
        agent_status_map = {}
        for agent_id, agent in self._agent_map.items():
            agent_status_map[agent_id] = AgentStatus.AVAILABLE
        sm = self._global_context.status_manager()
        for _, agent_id, status in sm.get_records():
            agent_status_map[agent_id] = status
        return agent_status_map

    def get_last_activity_timestamp(self) -> Optional[int]:
        """Get the timestamp of the last activity in the chorus.

        Returns:
            Optional[int]: The Unix timestamp of the last activity. Returns the last busy timestamp
                          if no status records exist, or None if no activity has occurred.
        """
        sm = self._global_context.status_manager()
        records = sm.get_records()
        if records:
            last_timestamp, _, _ = records[-1]
            return max(self._last_busy_timestamp, last_timestamp)
        else:
            return self._last_busy_timestamp


    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def start(self):
        """
        Start Chorus in a new thread. If a thread is already running, this method will do nothing.
        """
        if self._chorus_thread and self._chorus_thread.is_alive():
            return
        self._chorus_thread = threading.Thread(target=self.run)
        self._chorus_thread.start()
        # Wait for the thread to start
        time.sleep(1)
        while not self._chorus_thread.is_alive():
            time.sleep(0.1)
    
    def stop(self):
        """Stop Chorus and wait for it to finish.
        
        This method sets the stopping flag and waits for the chorus thread to complete
        if it exists and is running. This ensures a clean shutdown of all running processes.
        """
        self._stopping = True
        if self._chorus_thread and self._chorus_thread.is_alive():
            self._chorus_thread.join()
        self._stopping = False
        
    
    def cleanup(self, *args, **kwargs):
        """Clean up chorus resources and terminate all processes.
        
        This method is called when receiving SIGINT or SIGTERM signals. It terminates
        all running processes and exits the program.

        Args:
            *args: Variable length argument list for signal handler compatibility.
            **kwargs: Arbitrary keyword arguments for signal handler compatibility.
        """
        print("")
        print("Chorus is terminating...")
        for proc, _ in self.alive_processes:
            if proc.is_alive():
                proc.terminate()
        sys.exit(0)
