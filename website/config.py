import configparser
from path import PATH
from bitfield import BitField
from interface import Interface

class RWState(BitField):
    read = False
    write = True

def config(file: str, state=RWState()) -> configparser.ConfigParser:
    if cfg := config._static.get(file, False):
        return cfg
    cfg = configparser.ConfigParser(allow_no_value=True, interpolation=configparser.ExtendedInterpolation())
    fpath = f"{PATH}resource/config/{file}"
    cfg.read(fpath)
    config._static[file] = cfg
    def write():
        with open(fpath, "w") as f:
            cfg.write(f)
    Interface.terminate.schedule(write)
    return cfg
config._static = {}
@Interface.Repeat
async def _write_cfg():
    for p,c in config._static.items():
        async with Interface.AIOFile(f"{PATH}resource/config/{p}", "w") as f:
            c.write(f)
_write_cfg.delay = 60
_write_cfg()
