from engine.event.event import Event

__all__ = ["Layer", "LayerStack"]

class Layer:

    def update(self):
        pass
    def event(self, event: Event):
        pass

class LayerStack:

    def __init__(self):
        self.layers = []
    
    def append(self, layer: Layer):
        self.layers.append(layer)
    
    def pop(self) -> Layer:
        return self.layers.pop()

    def update(self):
        for layer in self.layers:
            layer.update()

    def event(self, event: Event):
        for layer in reversed(self.layers):
            layer.event(event)