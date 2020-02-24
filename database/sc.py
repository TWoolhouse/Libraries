import re

esc_char = "\\" # escape character
sc = {
"esc":esc_char,
# "comment":";",
"bracket_open":"(",
"bracket_close":")",
"brace_open":"{",
"brace_close":"}",
"table":"%",
"insert":">",
"update":"^",
"delete":"<",
"query":"?",
"ref":"$",
"next":",",
"type":":",
"link":"@",
"index":":",
"and":"+",
"or":"/",
"not":"-",
"is":"=",
"like":"~",
}
special_chars = [sc[k] for k in sc]

def convert(string, to=True):
    if to:
        return re.sub("{}[{}]".format(re.escape(esc_char), "".join(map(re.escape, special_chars))), lambda x: "__SC"+str(special_chars.index(x.group(0)[1:]))+"__", string) # deal with special characters
    return re.sub("__SC\d+__", lambda x: special_chars[int(x.group(0)[4:-2])], string, 0, re.I)
def escape(name):
    return re.escape(sc[name])
def search(name, string, *params, pre=True):
    # print("".join((str(i) for i in params))+escape(name), string)
    if pre:
        return re.search("".join((str(i) for i in params))+escape(name), string)
    return re.search(escape(name)+"".join((str(i) for i in params)), string)
def all(name, string, *params, pre=True):
    if pre:
        return re.finditer("".join((str(i) for i in params))+escape(name), string)
    return re.finditer(escape(name)+"".join((str(i) for i in params)), string)
def replace(name, repl, string, *params, pre=True):
    if pre:
        return re.sub("".join((str(i) for i in params))+escape(name), repl, string)
    return re.sub(escape(name)+"".join((str(i) for i in params)), repl, string)
def split(name, string, count=0, *params, pre=True):
    if pre:
        return re.split("".join((str(i) for i in params))+escape(name), string, count)
    return re.split(escape(name)+"".join((str(i) for i in params)), string, count)
def join(name, iter):
    return sc[name].join(iter)
