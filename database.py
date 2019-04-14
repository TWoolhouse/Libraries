from Database import sc
from Database import generate
import iofile

FILE = "database"
sql = iofile.sql(FILE)

def path(path="database"):
    iofile.path(path)

def file(file):
    global FILE, sql
    FILE = file
    sql.file_name = FILE

def gen(ifile, ofile=FILE):
    generate.generate(ifile, ofile)

for t in sql.select("__metadata__", cols="name"):
    print(t[0].title()+":", sql.select(t[0].title()))
