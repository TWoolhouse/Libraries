from Database import sc
import iofile

def _iter(func, index, item, *args):
    for a in args:
        item = func(*a[:index], item, *a[index:])
    return item

class Table:
    def __init__(self, name, *columns):
        self.name, self.columns = name.title(), list(columns)
    def __repr__(self):
        return "{}: {}".format(self.name, ", ".join((str(i) for i in self.columns)))

    class Column:
        def __init__(self, name, type=None, link=None):
            self.name, self.type, self.link = name.lower(), type.upper(), link
        def __repr__(self):
            return "{}, {}, {}".format(self.name, self.type, self.link)
    class Link:
        def __init__(self, parent, column):
            self.parent, self.column = parent.title(), column.lower()
        def __repr__(self):
            return "{} : {}".format(self.parent, self.column)

class Database:
    def __init__(self, name):
        self.name = name
        self.sql = iofile.sql(name)

    def create(self):
        self.sql.table("__metadata__", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", "name TEXT", "columns INTEGER")
        self.sql.table("__metametadata__", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", "tid INTEGER NOT NULL", "loc INTEGER", "name TEXT", "type TEXT", "link TEXT", "FOREIGN KEY (tid) REFERENCES __metadata__(id)")
        self.sql.command("VACUUM")
    def insert(self, table):
        self.sql.insert("__metadata__", table.name, len(table.columns), parameters=("name", "columns"))
        tid = self.sql.select("__metadata__", table.name, cols="id", conditional="name = ?", all=False)[0]
        for i in range(len(table.columns)):
            self.sql.insert("__metametadata__", tid, i, table.columns[i]["name"], table.columns[i]["type"], table.columns[i]["link"] if table.columns[i]["link"] == None else sc.sc["link"].join(table.columns[i]["link"]), parameters=("tid", "loc", "name", "type", "link"))
    def select(self, table):
        pass

    class table:
        def create(table):
            args = [(i["name"], i["type"]) for i in table.columns]
            links = [(i["name"], *i["link"]) for i in table.columns if i["link"] != None]
            self.sql.table(table.name, "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", *("{} {}".format(*i) for i in args), *("FOREIGN KEY ({}) REFERENCES {}({})".format(*i) for i in links))
            self.insert(table)
            return table
    class element:
        def select(table):
            pass
        def insert(table):
            arguments = []
            parameters = []

            for e in data:
                if table.columns[e].link != None:
                    arg = self.sql.select(table.columns[e].link[0], *data[e][0], cols=table.columns[e].link[1], conditional=data[e][1], all=False)[0]
                else:
                    arg = data[e]
                arguments.append(arg)
                parameters.append(table.columns[e].name)

            self.sql.insert(table.name, *arguments, parameters=parameters)
        def update(table):
            self.sql.update(table.name, arguments=data, parameters=clause[0], conditional=clause[1])

class Conversion:
    def __init__(self, database):
        self.table = None
        self.database = database

    def convert(self, data):
        print("INS:", data)
        data = sc.convert(data)
        for i in (self.category, self.update, self.element):
            res = i(data)
            if res:
                print(*res)
                return True
        return False

    def category(self, data):
        res = list(sc.all("cat", data))
        if not res or not res[0].span() == sc.search("cat", data, "\A").span():
            return False
        elif len(res) == 1:
            title = data[len(sc.sc["cat"]):]
            cats = sql.select("__metametadata__", sql.select("__metadata__", title, cols="id", conditional="name = ?", all=False)[0], cols="loc, name, type, link", conditional="tid = ?")
            cats = [{"name":i[1], "type":i[2], "link":self.table_link(i[3])} for i in sorted(cats)]
            set_table([title.title(), cats])
        else:
            data = sc.split("cat", data[len(sc.sc["cat"]):], 1)
            title = data[0]
            cats = sc.split("next", data[1])
            for i in range(len(cats)):
                cats[i] = self.cat_col(cats[i])
            self.table = Table(title, *cats)
            self.database.(table)
        return ("TBL:", self.table)

    def element(self, data):
        data = sc.split("next", data)
        data = Conversion.index(data)
        data.sort()
        data = {e[0]: Conversion.reference(e[1]) if table[1][e[0]]["link"] != None else e[1] for e in data}
        add_element(table, data)
        return ("ELM:", table[0], data)

    def update(self, data):
        res = list(sc.all("update", data))
        if not res or not res[0].span() == sc.search("update", data, "\A").span():
            return False
        elif len(res) == 1:
            clause, data = [(), None], data[len(sc.sc["update"]):]
        else:
            clause, data = sc.split("update", data[len(sc.sc["update"]):], 1)
            clause = Conversion.reference(clause)
        data = sc.split("next", data)
        data = Conversion.index(data)
        data.sort()
        data = {e[0]: Conversion.reference(e[1]) if table[1][e[0]]["link"] != None else e[1] for e in data}
        alter_element(table, clause, data)
        return ("UPD:", table[0], clause, data)

    def table_column(self, data):
        data = self.identify(data, "type", "link")
        data = {
            "name": data["data"].lower(),
            "type": self.type(" ".join(data["type"])),
            "link": self.table_link(sc.join("link", data["link"]))
        }
        return Table.Column(data["name"], data["type"], data["link"])

    def table_link(self, data):
        if data:
            return Table.Link(*sc.split("link", data, 1))
        return None

    def identify(self, data, *chars):
        res = {"data":data}
        for c in chars:
            res[c] = list(sc.all(c, data, "[^", *(sc.sc[i] for i in chars), "]*(?=([", *(sc.sc[i] for i in chars), "]|$))", pre=False))
            for m in res[c]:
                x = data[:m.span()[0]]
                if len(x) < len(res["data"]):
                    res["data"] = x
            res[c] = [i.group(0)[1:] for i in res[c]]
        return res

    def type(self, data):
        if data:
            return data.upper()
        return None

    def index(self, data):
        nlbl = []
        res = []
        for d in data:
            if sc.search("index", d, "\A\d+"):
                d = sc.split("index", d)
                d[0] = int(d[0])
                res.append(d)
            else:
                nlbl.append(d)
        for d in nlbl:
            i = 0
            while i in (j[0] for j in res):
                i += 1
            res.append([i, d])
        return res

    def logic(self, data, op): # take iter, return iter
        res = []
        for i in data:
            if sc.sc[op] == i:
                res.append(i)
            else:
                x = sc.split(op, i)
                for j in range(len(x)):
                    res.append(x[j])
                    if j+1 != len(x):
                        res.append(sc.sc[op])
        return res

    def reference(self, data):
        parameters, conditional = [], []

        data = [data]
        for i in ("and", "or"):
            data = Conversion.logic(data, i)

        for e in data:
            if e in map(sc.sc.__getitem__, ("and", "or")):
                conditional.append(_iter(sc.replace, 2, e, ("and", "AND"), ("or", "OR")))
            else:
                x = sc.split("link", e)
                x[1] = _iter(sc.replace, 2, x[1], ("like", " LIKE ?"), ("equal", " IS ?"))
                parameters.append(x[0])
                conditional.append(x[1])
        return (parameters, " ".join(conditional))

def generate(database, ifile, new=True):
    if new:
        database.sql.new()
        database.create()

    data = iofile.read.text(ifile)
    for line in data:
        if not line:
            continue
        Conversion.convert(line)

"""ifile example
?People?fname:TEXT#lname:TEXT
Gordon#Freeman
1:Johnson#0:Cave
Caroline#Johnson

?Info?pid:INTEGER NOT NULL@People(id)#status:TEXT
Gordon@fname=#stasis
Johnson@id@lname=&Cave@fname=#dead
Caroline@id@fname=#GLaDOS
"""
