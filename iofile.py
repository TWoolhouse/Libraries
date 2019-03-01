import sqlite3
import pickle
import json

PATH = ""

def path(val):
    global PATH
    PATH = str(val)

class BaseClass:

    def __init__(self, file_name):
        self.file_name = file_name

    def __str__(self):
        return str(self.file_name)
    def __repr__(self):
        return repr(self.file_name)
    def __add__(self, other):
        return self.file_name+other
    def __radd__(self, other):
        return other+self.file_name

class read(BaseClass):

    def text(file_name, split_char="", ext="txt"):
        with open("{}{}.{}".format(PATH, file_name, ext), "r") as file:
            return [(line.strip() if split_char == "" else line.strip().split(split_char)) for line in file]

    def bin(file_name, ext="txt"):
        with open("{}{}.{}".format(PATH, file_name, ext), "rb") as file:
            return file.read()

    def pickle(file_name, ext="txt"):
        with open("{}{}.{}".format(PATH, file_name, ext), "rb") as file:
            return pickle.load(file)

    def json(file_name, ext="json"):
        with open("{}{}.{}".format(PATH, file_name, ext), "r") as file:
            return json.load(file)

    def cfg(file_name, ext="cfg"): # wip
        with open("{}{}.{}".format(PATH, file_name, ext), "r") as file:
            d = {}
            sub = None

            for line in file:
                line = line.strip()

                if line == "": # getting rid of empty lines
                    continue

                elif line[0] == "[" and line[-1] == "]": # setting sub categories
                    sub = line[1:-1]
                    if sub not in d:
                        d[sub] = {}
                    continue

                #spliting into key and value
                line = line.split(" = ", 1)
                if len(line) == 1:
                    line.append("None")

                # type checking
                try:
                    if "." in line[1]:  line[1] = float(line[1]) # float
                    else:   line[1] = int(line[1]) # int
                except ValueError:
                    line[1] = (True if line[1].lower() in ["yes", "true"] else (False if line[1].lower() in ["no", "false"] else line[1])) # bool
                    line[1] = None if line[1] == "None" else line[1]

                try:
                    d[sub][line[0]] = line[1]
                except KeyError:
                    raise KeyError("No header was given for data. Data invalid.")
        return d

class write(BaseClass):

    def text(file_name, data, split_char="", ext="txt"):
        with open("{}{}.{}".format(PATH, file_name, ext), "w") as file:
            for line in data:
                file.write((str(line) if split_char == "" else split_char.join(str(i) for i in line))+"\n")

    def bin(file_name, data, ext="txt"):
        with open("{}{}.{}".format(PATH, file_name, ext), "wb") as file:
            file.write(data)

    def pickle(file_name, data, ext="txt"):
        with open("{}{}.{}".format(PATH, file_name, ext), "wb") as file:
            pickle.dump(data, file)

    def json(file_name, data, ext="json"):
        with open("{}{}.{}".format(PATH, file_name, ext), "w") as file:
            json.dump(data, file)

    def cfg(file_name, data, ext="cfg"):
        with open("{}{}.{}".format(PATH, file_name, ext), "w") as file:
            for sub in data:
                if type(data[sub]) == dict:
                    file.write("[{}]\n".format(sub))
                    for line in data[sub]:
                        file.write("{} = {}\n".format(line, "None" if data[sub][line] == None else data[sub][line]))
                    file.write("\n")
                else:
                    file.write("{} = {}\n".format(sub, "None" if data[sub] == None else data[sub]))

class sql(BaseClass):
    """ Nowhere near finished """

    def new(file_name, ext="db"):
        file = open("{}{}.{}".format(PATH, file_name, ext), "w")
        file.close()

    def table(file_name, table, *columns, ext="db"):
        with sqlite3.connect("{}{}.{}".format(PATH, file_name, ext)) as file:
            c = file.cursor()
            return c.execute("CREATE TABLE {} ({})".format(table, ", ".join(columns)))

    def command(file_name, text, ext="db"):
        with sqlite3.connect("{}{}.{}".format(PATH, file_name, ext)) as file:
            c = file.cursor()
            return c.execute(text)

    def insert(file_name, table, *arguments, parameters=(),ext="db"):
        with sqlite3.connect("{}{}.{}".format(PATH, file_name, ext)) as file:
            c = file.cursor()
            #command = "INSERT INTO {} {} VALUES ({})".format(table, ("("+(", ".join(parameters))+")" if parameters else ""), ", ".join(("?" for i in range(len(arguments)))))
            return c.execute("INSERT INTO {} {} VALUES ({})".format(table, ("("+(", ".join(parameters))+")" if parameters else ""), ", ".join(("?" for i in range(len(arguments))))), arguments)

    def select(file_name, table, *parameters, cols="*", conditional=None, all=True, ext="db"):
        with sqlite3.connect("{}{}.{}".format(PATH, file_name, ext)) as file:
            c = file.cursor()
            #command = "SELECT {} FROM {}{}".format(cols, table, "" if conditional == None else " WHERE {}".format(conditional))
            c.execute("SELECT {} FROM {}{}".format(cols, table, "" if conditional == None else " WHERE {}".format(conditional)), parameters)
            return c.fetchall() if all else c.fetchone()
