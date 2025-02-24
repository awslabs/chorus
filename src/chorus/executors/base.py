from abc import ABC
from abc import abstractmethod
from typing import Any

from chorus.data.data_types import ActionData


class ToolExecutor(ABC):

    @abstractmethod
    def execute(self, action: ActionData) -> Any:
        """
        Execute an action.
        """
