
from typing import Any, Tuple
from chorus.config.registrable import Registrable
from chorus.util.agent_naming import get_unique_agent_name
import uuid
import hashlib


class AgentMeta(Registrable):
    """
    A metaclass for agent definitions that allows delayed initialization.
    
    This metaclass overrides the standard instance creation process to store
    initialization arguments without immediately calling __init__. This enables
    agent definitions to be created first and initialized later, which is useful
    for dependency injection and configuration management in agent systems.
    """

    def __new__(cls, *args, **kwargs):
        """Create a new agent without initializing it (delayed initialization).
        """
        obj = super().__new__(cls)
        # Save init args
        obj._init_args = args
        obj._init_kwargs = kwargs
        obj._agent_name = None
        obj._agent_uuid = None
        return obj

    def get_name(self) -> str:
        """Get the name of the agent.

        Returns:
            str: The name of the agent.
        """
        if self._agent_name is None:
            self._agent_name = get_unique_agent_name()
        return self._agent_name
    
    def name_to_identifier(self, name: str) -> str:
        """Convert a name to an identifier.
        
        Args:
            name (str): The name to convert.
        """
        return name
    
    def identifier(self) -> str:
        """Get the identifier of the agent.
        
        Returns:
            str: The identifier of the agent.
        """
        return self.name_to_identifier(self.get_name())
    
    def name(self, name: str) -> 'AgentMeta':
        """Set the name of the agent. Returns self to allow method chaining.

        Args:
            name (str): The new name for the agent.
        """
        self._agent_name = name
        return self


    def initialize(self):
        """
        Initialize the instance with the previously stored arguments.
        
        This method calls the instance's __init__ method with the arguments
        that were stored during instance creation.
        """
        self.__init__(*self._init_args, **self._init_kwargs)

    def __str__(self):
        """
        Return a string representation of the agent.
        
        Returns:
            A string with meaningful information about the agent, including its
            name, type, and initialization parameters if available.
        """
        agent_id = self.identifier()

        class_name = self.__class__.__name__
        
        # Format positional arguments
        args_str = []
        for arg in self._init_args:
            if isinstance(arg, str):
                args_str.append(f'"{arg}"')
            else:
                args_str.append(f'{arg}')
        
        # Format initialization parameters as key=value pairs
        init_params = []
        for key, value in self._init_kwargs.items():
            if isinstance(value, str):
                init_params.append(f'{key}="{value}"')
            else:
                init_params.append(f'{key}={value}')
        
        # Combine args and kwargs
        all_params = []
        if args_str:
            all_params.extend(args_str)
        if init_params:
            all_params.extend(init_params)
            
        params_str = ", ".join(all_params)
        
        # Format as class_name(arg1, arg2, param1="value1", param2=value2)
        return f"{agent_id}<{class_name}({params_str})>"
    
    def get_agent_class_uuid(self) -> str:
        """
        Get a unique identifier for this agent class instance.
        
        This method generates a UUID based on the string representation of the agent,
        which includes the class name and initialization parameters.
        
        Returns:
            A string containing a UUID derived from the agent's string representation.
        """
        if self._agent_uuid is None:
            # Generate a deterministic UUID based on the string representation
            agent_str = str(self)
            hash_obj = hashlib.md5(agent_str.encode())
            self._agent_uuid = str(uuid.UUID(hex=hash_obj.hexdigest()))
        return self._agent_uuid
    

    def get_init_args(self) -> Tuple[Any, ...]:
        """
        Get the initialization arguments for the agent.
        
        Returns:
            A tuple containing the initialization arguments.
        """
        return self._init_args, self._init_kwargs