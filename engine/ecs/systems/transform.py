from engine.ecs.system import System
from engine.ecs.components import Transform as CTransform

class Transform(System):

    def update(self):
        return
        for component in self.components(CTransform):
            pass
            # component._edit = [False, False, False]