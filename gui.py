import tkinter as tk
import tkinter.messagebox as tkm
import tkinter.simpledialog as tkd
from collections import deque
from typing import Callable, Any

class Window(tk.Tk):
    """Tk root Window"""

    def __init__(self, title: str="Title", x: int=800, y: int=800, font: str="TkDefaultFont", resolution: int=10, parent=None):
        """Title and Geometry """
        super().__init__()
        self.title(title)
        self.geometry(str(x)+"x"+str(y))
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.option_add("*Font", font)
        self.pages: dict[str, Page] = {}
        self.active: Page = None
        self.parent = parent
        self.loop_resolution = resolution
        self._loop_callbacks: deque[Callable[[], Any]] = deque()
        self.after(self.loop_resolution, self.loop)

    def show_page(self, page: str):
        """Takes a name and raises the Page to the front and calls Page.show()"""
        try:
            self.active = self.pages[page]
        except KeyError as e:
            raise KeyError("'{}' is not a page in this Window".format(page))
        self.pages[page]._show()

    def add_page(self, page: 'Page'):
        """Takes a Page and adds it to the Windows stack of pages"""
        self.pages[page.name] = page
        page.grid(row=1, column=1, sticky="nsew")

    def __getitem__(self, key: str) -> 'Page':
        return self.pages[key]

    def loop(self):
        while self._loop_callbacks:
            self._loop_callbacks.popleft()()
        self.after(self.loop_resolution, self.loop)

    def call(self, func: Callable[[], Any]):
        self._loop_callbacks.append(func)

class Page(tk.Frame):
    """Tk Frame"""

    def __init__(self, parent: Window, name: str, *args):
        """Parent Window and the Name to be used in the dict of pages"""
        self.name = name
        self.parent = parent
        super().__init__(self.parent)
        self.parent.add_page(self)
        self.widgets: dict[str, tk.Widget] = {}
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(9999, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(9999, weight=1)
        self.setup(*args)

    def __getitem__(self, key: str) -> tk.Widget:
        return self.widgets[key]

    def __setitem__(self, key: str, value: tk.Widget):
        self.widgets[key] = value

    def add(self, widget: tk.Widget, name: str="_temp", **options):
        """tk.Wiget, name in widget dict, grid options"""
        self.widgets[name] = widget
        if "sticky" not in options:
            options["sticky"] = "nsew"
        elif options["sticky"] is None:
            del options["sticky"]
        self.widgets[name].grid(options)

    def remove(self, widget: str):
        self.widgets[widget].grid_remove()

    def edit(self, widget: str, key: str, value):
        """widget name, value to edit, value"""
        self.widgets[widget][key] = value

    def _show(self):
        """Called when raised to the front of the stack"""
        self.tkraise()
        self.show()

    def show_page(self, page: str):
        """Calls parent.show_page() with page"""
        self.parent.show_page(page)

    def show(self):
        pass

    def setup(self):
        pass

    def update(self):
        pass

class Dialog(tkd.Dialog):
    def __init__(self, parent, title="Dialog", **inputs):
        self.inputs = inputs
        super().__init__(parent, title.title())

    def body(self, master):

        self.entries = []

        for i,k in enumerate(self.inputs.items()):
            tk.Label(master, text=str(k[0]).title()).grid(row=i)
            e = tk.Entry(master)
            e.grid(row=i, column=1)
            self.entries.append((e, k[1]))

        return self.entries[0][0]

    def validate(self):
        _res = []
        for e,t in self.entries:
            try:
                if t:
                    _res.append(t(e.get()))
                else:
                    _res.append(e.get())
            except ValueError:
                tkm.showwarning("Bad input", "Illegal values\nPlease try again")
                return 0

        self.result = _res
        return 1

def cmd(func, *args, **kwargs):
    """Takes a function followed by its arguments"""
    def command(*a, **ka):
        return func(*args, **kwargs)
    return command

if __name__ == "__main__":
    app = Window("Test App")
    page = Page(app, "home")
    page.add(tk.Label(page, text="Hello and Welcome"), row=1, column=1, sticky="nsew")
    page.add(tk.Button(page, text="Counting Page", command=lambda: page.show_page("counter")), row=2, column=1, pady=15, sticky="nsew")
    page = Page(app, "counter")
    page.add(tk.Button(page, text="Home", command=lambda: page.show_page("home")), row=1, column=1, pady=15, sticky="nsew")
    page.add(tk.Label(page, text="0"), name="output", row=3, column=1, sticky="nsew")
    page.add(tk.Button(page, text="Count", command=lambda: page.edit("output", "text", str(int(page["output"]["text"])+1))), row=2, column=1, pady=15, sticky="nsew")
    app.show_page("home")
    app.mainloop()
