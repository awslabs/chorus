class BasePrompter(object):
    @classmethod
    def get_subclass(cls, name: str):
        for subclass in cls.__subclasses__():
            if subclass.__name__.split(".")[-1] == name:
                return subclass
        return None
