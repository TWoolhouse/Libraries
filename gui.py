import tkinter as tk
import tkinter.messagebox as tkm
import tkinter.simpledialog as tkd

class Window(tk.Tk):
    """Tk root Window"""

    def __init__(self, title="Title", x=800, y=800, font="TkDefaultFont", parent=None):
        """Title and Geometry """
        super().__init__()
        self.title(title)
        self.geometry(str(x)+"x"+str(y))
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.option_add("*Font", font)
        self.pages = {}
        self.active = None
        self.parent = parent

    def show_page(self, page):
        """Takes a name and raises the Page to the front and calls Page.show()"""
        try:
            self.active = self.pages[page]
            self.pages[page]._show()
        except KeyError as e:
            raise KeyError("'{}' is not a page in this Window".format(page))

    def add_page(self, page):
        """Takes a Page and adds it to the Windows stack of pages"""
        self.pages[page.name] = page
        page.grid(row=1, column=1, sticky="nsew")

    def __getitem__(self, key):
        return self.pages[key]

    def update(self):
        self.active.update()
        super().update()

class Page(tk.Frame):
    """Tk Frame"""

    def __init__(self, parent, name, *args):
        """Parent Window and the Name to be used in the dict of pages"""
        self.name = name
        self.parent = parent
        super().__init__(self.parent)
        self.parent.add_page(self)
        self.wigets = {}
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(9999, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(9999, weight=1)
        self.setup(*args)

    def __getitem__(self, key):
        return self.wigets[key]

    def __setitem__(self, key, value):
        self.wigets[key] = value

    def add(self, wiget, name="_temp", **options):
        """tk.Wiget, name in wiget dict, grid options"""
        self.wigets[name] = wiget
        self.wigets[name].grid(options)

    def edit(self, wiget, key, value):
        """wiget name, value to edit, value"""
        self.wigets[wiget][key] = value

    def _show(self):
        """Called when raised to the front of the stack"""
        self.tkraise()
        self.show()

    def show_page(self, page):
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

def cmd(func, *options, **kwoptions):
    """Takes a function followed by its arguments"""
    def command(*args, **kwargs):
        return func(*options, **kwoptions)
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
