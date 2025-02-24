import abc
from typing import Dict, Optional

# from chorus.core.simulator import MultiAgentSimulator


class MultiAgentStopCondition(metaclass=abc.ABCMeta):
    """Base class for multi-agent stop conditions.

    Defines conditions that determine when to stop multi-agent interactions.
    """

    def __init__(self):
        self._simulator = None

    def runner(self):
        """Get the current runner.

        Returns:
            Runner: The runner managing the agents.
        """
        return self._runner

    def set_runner(self, runner):
        """Set the runner reference.

        Args:
            runner (Runner): The runner managing the agents.
        """
        self._runner = runner

    @abc.abstractmethod
    def stop(self) -> bool:
        """Check if the stop condition is met.

        Returns:
            bool: True if the condition is met and execution should stop.

        Raises:
            NotImplementedError: This is an abstract method.
        """
        pass
