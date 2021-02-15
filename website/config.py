import configparser
from path import PATH
from bitfield import BitField
from interface import Interface

class RWState(BitField):
    read = False
    write = True

class Config(configparser.ConfigParser):
    rwstate: RWState = RWState()

def config(file: str, read=False, write=True) -> Config:
    if cfg := config._static.get(file, False):
        return cfg
    state = RWState(read=read, write=write)
    cfg = configparser.ConfigParser(allow_no_value=True, interpolation=configparser.ExtendedInterpolation())
    fpath = f"{PATH}resource/config/{file}"
    cfg.read(fpath)
    config._static[file] = cfg
    def write():
        with open(fpath, "w") as f:
            cfg.write(f)
    if state.write:
        Interface.terminate.schedule(write)
    cfg.rwstate: RWState = state
    return cfg
config._static = {}

@Interface.Repeat
async def _reload_cfg():
    for p,c in config._static.items():
        if c.rwstate.write:
            async with Interface.AIOFile(f"{PATH}resource/config/{p}", "w") as f:
                c.write(f)
        elif c.rwstate.read:
            async with Interface.AIOFile(f"{PATH}resource/config/{p}", "r") as f:
                c.read_file(f)
_reload_cfg.delay = 60
_reload_cfg()
