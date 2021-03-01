from ..entity import Entity
from ..component import Component

from ..core.transform import Transform
from ...render.primitive import Primitive

from vector import Vector

from ...core.application import app as Application
from ... import error
from ..._settings.render import Setting

__all__ = ["Render", "RenderMulti", "RenderBatch"]

class Render(Component):

    def __init__(self, primative: Primitive, volatile=False, layer:int=0):
        self._original = primative
        self._drawn = self._original

        self._vol: bool = volatile
        self._vcache: tuple = self._original._volatile() if self._vol else None

        self._update = True

    def update(self):
        self._update = True

    def initialize(self):
        self.transform: Transform = self.Get(Transform)
        self._u_transform()
        self._u_drawn_primative()
        self.update()

    def _u_transform(self) -> [Vector, float, Vector]:
        self._global_transform = (self.transform.position_global, self.transform.rotation_global, self.transform.scale_global)
        return self._global_transform

    def _u_drawn_primative(self):
        self._drawn = self._original.Transform(*self._global_transform)

    def _volatile(self) -> bool:
        vol = self._original._volatile()
        if vol == self._vcache:
            return False
        self._vcache = vol
        return True

    def primative(self) -> Primitive:
        return self._original

    def __repr__(self) -> str:
        return f"{super().__repr__()}<{self._original}>"

class RenderMulti(Component):
    def __init__(self, *renders: Render, transform: Transform=None):
        for c in renders:
            if not isinstance(c, Render):
                raise error.ecs.ComponentTypeError(c, Render)
        self.components: tuple[Render] = renders
        self.__transform: Transform = transform

    def initialize(self):
        self.__s_app_world = Application().world
        self.__entity = self.__s_app_world.instantiate(*self.components, parent=self.entity, transform=self.__transform, id=False)
        self.__transform = self.__entity.Get(Transform)

    @property
    def transform(self) -> Transform:
        return self.__transform

    def terminate(self):
        self.__s_app_world.destroy(self.__entity)

    def __getitem__(self, key: int) -> Render:
        return self.components[key]

class RenderBatch(Component):
    def __init__(self, *renders: (Render, Transform)):
        _type = True # 0 - Render, 1 - Transform
        comps = []
        self.__transforms: list[Transform] = []
        for c in renders:
            _type = not _type
            if _type:
                if isinstance(c, (Transform, type(None))):
                    self.__transforms.append(c)
                    continue
                else:
                    self.__transforms.append(None)
                    _type = not _type
            if not isinstance(c, (Render, RenderMulti)):
                raise error.ecs.ComponentTypeError(c, Render)
            comps.append(c)
        while len(self.__transforms) < len(comps):
            self.__transforms.append(None)
        self.components: tuple[Render] = tuple(comps)

    def initialize(self):
        self.__s_app_world = Application().world
        self.__entities = []
        for i, r, t in zip(*zip(*enumerate(self.components)), self.__transforms):
            self.__entities.append(self.__s_app_world.instantiate(r, parent=self.entity, transform=t, id=False))
            self.__transforms[i] = self.__entities[-1].Get(Transform)

    def terminate(self):
        for e in self.__entities:
            self.__s_app_world.destroy(e)

    def __getitem__(self, key: int) -> Render:
        return self.components[key]

    def transform(self, key: (int, Render)) -> Transform:
        if isinstance(key, int):
            return self.__transforms[key]
        return self.__transforms[self.components.index(key)]
