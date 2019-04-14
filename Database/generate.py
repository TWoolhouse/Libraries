from Database import sc
import iofile

sql = iofile.sql("database")

def create_table(name, categories):
    # print("TBL:", name, categories)
    args = ["{} {}".format(i["name"], i["type"]) for i in categories]
    links = ["FOREIGN KEY ({}) REFERENCES {}({})".format(i["name"], *i["link"]) for i in categories if i["link"] != None]
    sql.table(name, "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", *args, *links)
    sql.insert("__metadata__", name, ", ".join(["id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", *args, *links]), parameters=("name", "columns"))

def add_element(table, row):
    # print("ELM:", table[0], row)
    arguments = []
    parameters = []

    for r in row:
        if table[1][r[0]]["link"] != None:
            params = []
            cols = set()
            conds = []
            x = []
            y = sc.split("and", r[1])
            for i in y:
                x.append(i)
                if len(y) > 1:
                    x.append("AND")
            if len(y) > 1:
                x.pop()
            _c = []
            for i in range(len(x)):
                if x[i] != "AND":
                    y = sc.split("or", x[i])
                    for j in y:
                        _c.append(j)
                        if len(y) > 1:
                            _c.append("OR")
                    if len(y) > 1:
                        _c.pop()
                else:
                    _c.append(x[i])

            for c in _c:
                if c in ("AND", "OR"):
                    conds.append(c)
                else:
                    c = sc.split("link", c)
                    params.append(c[0])
                    val = 0
                    if len(c) > 2:
                        cols.add(c[1])
                        val = 1
                    conds.append(sc.replace("not", sc.replace("like", sc.replace("equal", c[1+val], " IS "), " LIKE "), " NOT ")+"?")

            # print(params, cols, conds)
            arguments.append(sql.select(table[1][r[0]]["link"][0], *params, cols=", ".join(cols) if cols else table[1][r[0]]["link"][1], conditional=" ".join(conds), all=False)[0])
            parameters.append(table[1][r[0]]["name"])
        else:
            arguments.append(r[1])
            parameters.append(table[1][r[0]]["name"])

    # print(arguments, parameters)
    sql.insert(table[0], *arguments, parameters=parameters)

def generate(ifile, ofile="database"):
    sql.file_name = ofile
    sql.new()
    sql.table("__metadata__", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL", "name TEXT", "columns CLOB")
    data = iofile.read.text(ifile)
    table = None
    for line in data:
        if not line:
            continue
        line = sc.convert(line)

        if sc.search("cat", line, "\A"): # New table
            line = sc.split("cat", line[1:], 1)
            title = line[0]
            cat = sc.split("next", line[1])
            for i in range(len(cat)):
                segs = [sc.split("link", j) for j in sc.split("type", cat[i])]
                cat[i] = {
                    "name":segs[0][0].lower(),
                    "type":segs[1][0].upper() if len(segs) == 2 else "NONE",
                    "link":segs[0][1].title() if len(segs[0]) == 2 else segs[1][1].title() if len(segs) == 2 and len(segs[1]) == 2 else None
                }
                if cat[i]["link"]:
                    match = sc.re.search("\(.+\)", cat[i]["link"])
                    if match:
                        cat[i]["link"] = [cat[i]["link"][:match.start()], match.group(0)[1:-1].lower()]
                    else:
                        raise ValueError("No Reference: "+cat[i]["link"])
            table = [title.title(), cat]
            create_table(*table)

        else: # New element
            d = sc.split("next", line) # split up the cats
            for v in range(len(d)): # every item
                d[v] = sc.split("index", d[v], 1) if sc.search("index", d[v], "\A\d+") else [v, d[v]] # add the cat index per item
                d[v][0] = int(d[v][0]) # cat index set to int
                d[v][1] = d[v][1].strip() # remove leading and trailing whitespace characters
            d.sort()
            add_element(table, d)

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
