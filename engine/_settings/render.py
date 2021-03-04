import layer

class Setting:
    def __init__(self):
        self.layers = layer.Type("RenderLayer", )
        self.stack = layer.Stack(self.layers)
