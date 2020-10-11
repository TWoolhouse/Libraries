from .base import ECSError

__all__ = ["ComponentTypeError", "EntityLimitError", "GetComponentError", "InitializeComponent", "TerminateComponent"]

class ComponentTypeError(ECSError):
    def __init__(self, component, expected=None):
        self.component = component
        self.expected = expected

    def __str__(self) -> str:
        if self.expected is None:
            return f"{self.component} is not the correct type"
        return f"Expected: '{self.expected}' Got {self.component}"

class EntityLimitError(ECSError):

    def __init__(self, world, limit):
        self.world = world
        self.limit = limit

    def __str__(self) -> str:
        return "Entity Limit: {} reached in World: {}".format(self.limit, self.world)

class GetComponentError(ECSError):

    def __init__(self, entity, component):
        self.entity = entity
        self.component = component

    def __str__(self) -> str:
        return "{}<{}> Does not Exist".format(self.entity, self.component.__name__)

class InitializeComponent(ECSError):

    def __init__(self, entity, component, value):
        self.entity = entity
        self.component = component
        self.value = value

    def __str__(self) -> str:
        return "{}<{}> Failed to Initialize with '{}'".format(self.entity, self.component.__class__.__name__, self.value)

class TerminateComponent(ECSError):

    def __init__(self, entity, component, value):
        self.entity = entity
        self.component = component
        self.value = value

    def __str__(self) -> str:
        return "{}<{}> Failed to Terminate with '{}'".format(self.entity, self.component.__class__.__name__, self.value)

class ParentError(ECSError):

    def __init__(self, entity):
        self.entity = entity

    def __str__(self) -> str:
        return "{} Has no parent"