import re

esc_char = "$" # escape character
sc = {
"esc":esc_char, # escape character
"and":"&", # and
"or":"|", # or
"not":"!", # not
"next":"#", # next category
"index":":", # category index
"cat":"?", # category layout
"link":"@", # link to another table
"type":":", # value type for each category
"equal":"=", # Equality operator
"like":"~", # LIKE operator
}
special_chars = [sc[k] for k in sc]

def convert(string, to=True):
    if to:
        return re.sub("{}[{}]".format(re.escape(esc_char), "".join(map(re.escape, special_chars))), lambda x: "__SC"+str(special_chars.index(x.group(0)[1:]))+"__", string) # deal with special characters
    return re.sub("__SC\d+__", lambda x: special_chars[int(x.group(0)[4:-2])], string)
def escape(name):
    return re.escape(sc[name])
def search(name, string, *params):
    return re.search("".join((str(i) for i in params))+escape(name), string)
def replace(name, string, repl, *params):
    return re.sub("".join((str(i) for i in params))+escape(name), repl, string)
def split(name, string, count=0, *params):
    return re.split("".join((str(i) for i in params))+escape(name), string, count)
