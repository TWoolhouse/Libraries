import turtle

def setup_screen(func):
    def wrapper(title="Title", size=None, tracer=0):
        screen = func()
        screen.title(title)
        if size != None:
            screen.setup(*size)
        screen.tracer(tracer)
        screen.colormode(255)
        return screen
    return wrapper

def Screen(title="Title", size=None, tracer=0):
    """Returns a new turtle screen"""
    return turtle.Screen(title, size, tracer)

def Canvas(master):
    return turtle.ScrolledCanvas(master)

class RawTurtle(turtle.RawTurtle):

    def __init__(self, canvas):
        super().__init__(canvas)
        self.ht()
        self.pu()
        self.seth(90)
        self.speed("fastest")
        self.color(0,0,0)

class Turtle(turtle.Turtle):
    """A Turtle"""

    def __init__(self):
        super().__init__()
        self.ht()
        self.pu()
        self.seth(90)
        self.speed("fastest")
        self.color(0,0,0)

turtle.Screen = setup_screen(turtle.Screen)

if __name__ == "__main__":
    s = Screen(0)
    t = Turtle()
    t.dot()
    t.circle(50)
    s.mainloop()
