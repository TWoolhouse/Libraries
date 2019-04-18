from Database import sc
import iofile

class Table:
    def __init__(self, name, *columns):
        self.name, self.columns = name.title(), list(columns)
    def __repr__(self):
        return "{}: {}".format(self.name, " | ".join((str(i) for i in self.columns)))

    class Column:
        def __init__(self, name, type=None, link=None):
            self.name, self.type, self.link = name.lower(), type.upper(), link
        def __repr__(self):
            return "{}, {}, {}".format(self.name, self.type, self.link if self.link else "LINK")
    class Link:
        def __init__(self, parent, column):
            self.parent, self.column = parent.title(), column.lower()
        def __repr__(self):
            return "{} : {}".format(self.parent, self.column)

class Database:
    def __init__(self, name):
        self.name = str(name)
        self.sql = iofile.sql(self.name)

    def new(self):
        self.sql.new()
        self.sql.table("__metadata__", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", "name TEXT", "columns INTEGER")
        self.sql.table("__metametadata__", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", "tid INTEGER NOT NULL", "loc INTEGER", "name TEXT", "type TEXT", "link TEXT", "FOREIGN KEY (tid) REFERENCES __metadata__(id)")
        self.sql.command("VACUUM")

    def md_insert(self, table):
        pass
    def table_create(self, table):
        pass
    def table_load(self, name):
        tid = self.sql.select("__metadata__", name, cols="id", conditional="name = ?", all=False)[0]
        data = self.sql.select("__metametadata__", tid, cols="loc, name, type, link", conditional="tid = ?")
        return Table(name, *(Table.Column(i[1], i[2], Table.Link(*sc.split("link", i[3], 1)) if i[3] else None) for i in sorted(data)))
    def element_insert(self):
        pass
    def element_reference(self, *args):
        pass

class Convert:
    def __init__(self, database):
        self.db = database
        self.table = None

    def __call__(self, data):
        oper = self.start(data, "table", "insert", "update")
        if oper not in (None, "esc"):
            data = getattr(self, "con_"+oper)(data[len(sc.sc[oper]):])
        return data

    def start(self, data, *chars):
        for c in chars:
            if sc.search(c, data, "\A"):
                return c
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

    def con_table(self, data):
        data = sc.split("table", data, 1)
        if len(data) == 1:
            self.table = self.db.table_load(data[0])
        else:
            name = data[0]
            data = (self.identify(c, "type", "link") for c in sc.split("next", data[1]))
            data = (Table.Column(i["data"], " ".join(i["type"]), Table.Link(*i["link"]) if i["link"] else None) for i in data)
            self.table = Table(name, *data)
            self.db.table_create(self.table)
        return self.table

    def con_insert(self, data):
        data = sc.split("next", data)
        data = self._index(data)
        data = {e[0]: self.con_reference(e[1]) for e in data}
        return data

        # data = sc.split("next", data)
        # data = Conversion.index(data)
        # data.sort()
        # data = {e[0]: Conversion.reference(e[1]) if table[1][e[0]]["link"] != None else e[1] for e in data}
        # add_element(table, data)
        # return ("ELM:", table[0], data)

    def con_update(self, data):
        return data

    def _index(self, data):
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
        return sorted(res)

    def _logic(self, data, op):
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

    def con_reference(self, data):
        if self.start(data, "ref"):
            cond, param = sc.split("link", data, 1)
            # param = param
            cond = [cond]
            for op in ("and", "or"):
                cond = self._logic(cond, op)
            count = len([i for i in cond if i in map(sc.sc.__getitem__, ("and", "or"))]) + 1
            params = []
            print(cond, param)
            for i in range(count):
                x = self.con_reference(param)
                params.append(x[0])
                param = x[1]
            print(params)
            return params
        else:
            return sc.split("link", data, 1)

class Ref:
    def __init__(self, cond, *param):
        self.cond, self.param = cond, list(param)
    def __repr__(self):
        return "{} {}".format(self.cond, self.param)
    def evaluate(self):
        pass
