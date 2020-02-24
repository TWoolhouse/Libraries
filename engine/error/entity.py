from engine.error.base import EntityError

class EntityComponentError(EntityError):

    def __init__(self, entity, component, msg=""):
        self.entity, self.component, self.msg = entity, component, msg

    def __str__(self) -> str:
        return "{}<{}> -> {}".format(self.entity, self.component, self.msg)

class EntityComponentGetError(EntityComponentError):

    def __init__(self, entity, component):
        self.entity, self.component = entity, component

    def __str__(self) -> str:
        return "{}<{}> Does not Exist".format(self.entity, self.component.__name__)