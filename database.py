from Database import sc
import iofile

class Table:
    def __init__(self, name, *cols):
        self.name, self.cols = name.title(), list(cols)
    def __repr__(self):
        return "TBL: {}: {}".format(self.name, ", ".join((str(i) for i in self.cols)))
    class Column:
        def __init__(self, name, type, link):
            self.name, self.type, self.link = name.lower(), type.upper(), link
        def __repr__(self):
            return "{} - {} - {}".format(self.name, self.type, self.link)
        def insert(self):
            return "{} {}".format(self.name, self.type)
        class Link:
            def __init__(self, parent, column):
                self.parent, self.column = parent.title(), column.lower()
            def __repr__(self):
                return "{} - {}".format(self.parent, self.column)
            def insert_ref(self, fk):
                return "FOREIGN KEY ({}) REFERENCES {}({})".format(fk, self.parent, self.column)
            def insert_pair(self):
                return sc.join("link", (self.parent, self.column))
class Element:
    def __init__(self, *segs):
        self.segs = list(segs)
    def __repr__(self):
        return "{}".format(", ".join((str(i) for i in self.segs)))
    def evaluate(self, con):
        return (i.evaluate(con) for i in self.segs)
    class Segment:
        def __init__(self, index, data):
            self.index, self.data = index, data
        def __repr__(self):
            return "SEG: {}: {}".format(self.index, self.data)
        def evaluate(self, con):
            return self.data
    class Ref(Segment):
        def __init__(self, table, parent, col, condition, *args, index=None):
            self.index, self.table, self.parent, self.col, self.cond, self.args = index, table, parent, col.lower(), condition, list(args)
        def __repr__(self):
            return "REF: {}: {}: {}<{}> {} -> {}".format(self.index, self.table.name, self.parent, self.col, self.cond, self.args)
        def evaluate(self, con):
            # print(self)
            cond = ConCondition(con).convert(self.cond) # convert to sql
            params = []
            for a in self.args:
                if type(a) == type(self):
                    params.append(a.evaluate(con))
                else:
                    params.append(a)
            # print(self.parent, self.col, ":", cond, params)
            return con.db.row_select(self.parent, cond, *params, columns=self.col)[0]

class Database:
    def __init__(self, name):
        self.name = str(name)
        self.sql = iofile.sql(self.name)
        self.parser = Parser(self)

    def parse(self, iput):
        return self.parser(iput)

    def new(self):
        self.sql.new()
        self.sql.table("__metadata__", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", "name TEXT", "columns INTEGER")
        self.sql.table("__metametadata__", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", "tid INTEGER NOT NULL", "loc INTEGER", "name TEXT", "type TEXT", "link TEXT", "FOREIGN KEY (tid) REFERENCES __metadata__(id)")
        self.sql.command("VACUUM")

    def md_table_search(self, name):
        return self.sql.select("__metadata__", name.title(), conditional="name = ?", all=False)
    def md_column_search(self, tid):
        return self.sql.select("__metametadata__", tid, conditional="tid = ?")
    def md_table_insert(self, table):
        self.sql.insert("__metadata__", table.name, len(table.cols), parameters=("name", "columns"))
        tid = self.md_table_search(table.name)[0]
        for i in range(len(table.cols)):
            self.md_column_insert(tid, i, table.cols[i])
    def md_column_insert(self, tid, index, column):
        self.sql.insert("__metametadata__", tid, index, column.name, column.type, column.link if column.link == None else column.link.insert_pair(), parameters=("tid", "loc", "name", "type", "link"))

    def table_insert(self, table):
        self.sql.table(table.name, "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", *(c.insert() for c in table.cols), *(c.link.insert_ref(c.name) for c in table.cols if c.link))
        self.md_table_insert(table)
        return table
    def row_insert(self, table, elm, con):
        self.sql.insert(table.name, *elm.evaluate(con), parameters=(table.cols[i.index].name for i in elm.segs))
        return elm
    def row_select(self, name, condition, *parameters, columns="*", all=False):
        return self.sql.select(name, *parameters, cols=columns, conditional=condition, all=all)

class Parser:
    def __init__(self, db):
        self.db = db
        self.table = None

    def __call__(self, data):
        oper_funcs = {"esc":Con, "table":ConTable, "insert":ConInsert, "update":Con, "delete":Con, "query":ConQuery}
        oper = None
        for c in oper_funcs:
            if sc.search(c, data, "\A"):
                oper = c
                break
        else:
            return data
        return oper_funcs[oper](self).convert(data[len(sc.sc[oper]):])

    def next(self, data, char="next"):
        return [i.strip() for i in sc.split(char, data)]

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

    def index(self, data):
        nlbl = []
        res = []
        for d in data:
            if sc.search("index", d, "\A\d+"):
                d = sc.split("index", d, 1)
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

    def reduce(self, func, init, *args, index=0):
        for a in args:
            init = func(*a[:index], init, *a[index:])
        return init

class Con:
    def __init__(self, parser):
        self.parser = parser
    def __call__(self, *args, **kwargs):
        return self.convert(*args, **kwargs)
    def convert(self, data):
        return data

class ConTable(Con):
    def convert(self, data):
        segs = self.parser.next(data, "table")
        if len(segs) == 1:
            self.parser.table = self.lookup(segs[0])
        elif len(segs) == 2:
            self.parser.table = self.construct(*segs)
            self.parser.db.table_insert(self.parser.table)
        else:
            return segs
        return self.parser.table

    def lookup(self, name):
        tbl = self.parser.db.md_table_search(name)
        cols = sorted(self.parser.db.md_column_search(tbl[0]))
        table = Table(tbl[1], *(Table.Column(c[3], c[4], Table.Column.Link(*sc.split("link", c[5])) if c[5] else None) for c in cols))
        return table

    def construct(self, name, cols):
        cols = self.parser.next(cols)
        cols = (self.parser.identify(c, "type", "link") for c in cols)
        cols = (Table.Column(c["data"], " ".join(c["type"]), Table.Column.Link(*c["link"]) if c["link"] else None) for c in cols)
        return Table(name, *cols)

class ConInsert(Con):
    def convert(self, data):
        elms = self.parser.next(data)
        elms = self.parser.index(elms)
        elms = (self.element(*e) for e in elms)
        elm = Element(*elms)

        return self.parser.db.row_insert(self.parser.table, elm, self.parser)

    def element(self, index, data):
        if sc.search("ref", data, "\A"):
            seg = ConRef(self.parser).convert(index, data)
        # elif sc.search("query", data, "\A"):
        #     seg = ConQuery(self.parser).convert(data)
        else:
            seg = Element.Segment(index, data)
        return seg

class ConRef(Con):
    def convert(self, index, data):
        return self.cast_ref(self.parser.table, self.ref(self.parser.table, data)[0], index)

    def ref(self, table, data):
        # print("REF", data)
        if not sc.search("ref", data, "\A"):
            res = self.parser.identify(data, "link")
            # print("ELM", res, res["data"], len(res["data"]))
            return (res["data"], len(res["data"]))
        data = data[1:]
        count = sc.search("ref", data)
        lsi = sc.search("link", data).span()
        cond = data[count.span()[1] if count and count.span()[0] < lsi[0] else 0:lsi[0]]
        count = int(data[:count.span()[0]]) if count and count.span()[0] < lsi[0] else 1
        # print("SET", lsi, cond, count, data)
        offset = lsi[1]
        params = []

        for i in range(count):
            res = self.ref(table, data[offset:])
            # print("RES", offset, data[offset:], res, offset + res[1] + len(sc.sc["link"]))
            params.append(res[0])
            offset += res[1] + len(sc.sc["link"])

        return (cond, params), offset

    def cast_ref(self, table, data, index=0):
        # print(index, data, table)
        return Element.Ref(table, table.cols[index].link.parent, table.cols[index].link.column, data[0], *(self.cast_ref(ConTable(self.parser).lookup(table.cols[index].link.parent), i, index=0) if type(i) == tuple else i for i in data[1]), index=index)

class ConCondition(Con):
    def convert(self, data):
        data = self.logical(data)
        data = self.binary(data)
        return data

    def logical(self, data):
        return self.parser.reduce(sc.replace, data, *((i, " "+i.upper()+" ") for i in ("and", "or")), index=2)
    def binary(self, data):
        return self.parser.reduce(sc.replace, data, *((i, " "+i.upper()+" ?") for i in ("is", "like")), index=2)

class ConQuery(Con):
    def convert(self, data):
        print(data)
        data = self.query(data)
        print(data)
        return data

    def query(self, data):
        while True:
            q = sc.search("query", data)
            if q:
                data = self.query(data[q.span()[1]:])
            else:
                break

        end = list(sc.all("brace_close", data))
        end = end[-1].span() if end else [len(data)]*2
        rest = data[end[1]:]
        data = data[:end[0]]

        data = self.parse(data)
        data = data+rest
        return data

    def parse(self, data):
        t = sc.search("table", data)
        l = list(sc.all("link", data))
        r = sc.search("ref", data)
        fs = sc.search("brace_open", data)
        b = len([i for i in l if i.span()[0] < r.span()[0]])
        f = len([i for i in l if i.span()[0] > fs.span()[0]]) if fs else 0
        a = len(l)-b-f

        if t:
            l = sc.search("link", data)
            table = ConTable(self.parser).lookup(data[t.span()[1]:l.span()[0]])
            data = data[l.span()[1]:]
            b -= 1
        else:
            table = self.parser.table

        print(data)
        r = sc.search("ref", data)
        print("R:", r)
        fs = sc.search("brace_open", data)
        cols = data[:r.span()[0]]
        args = data[r.span()[1]:fs.span()[0] if fs else None]

        cols = sc.split("link", cols, count=b)
        args = sc.split("link", args, count=a)
        cond = args[0]
        args = args[1:]
        fmat = data[fs.span()[1]:] if fs else " ".join(["()"]*len(cols))

        print(" ")
        print(data)
        print(table)
        print(cols)
        print(cond)
        print(args)
        print(fmat)
        print(" ")

        return self.evaluate(table, cols, cond, args, fmat)

    def evaluate(self, table, cols, cond, args, fmat):
        res = self.parser.db.row_select(table.name, ConCondition(self.parser)(cond), *args, columns=", ".join(cols))
        return fmat.replace("(", "{").replace(")", "}").format(*res)
