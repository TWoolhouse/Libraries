import sinput
import subprocess
import time
import winsound
import keys

# cmd = "ffplay -loglevel quiet -nodisp \""+file+"\""
# os.system(cmd)
# song = subprocess.Popen(cmd)
# song.terminate()

_ffplay = "D:/Programs/ffmpeg/bin/ffplay.exe"
_winsound = True

try:
    subprocess.run(_ffplay, capture_output=True)
    _winsound = False
except FileNotFoundError: pass

class Song:
    def __init__(self, file, **kwargs):
        """ss: start, t: duration, volume: volume"""
        self.file = file.replace("\\", "/")
        x = self.file.split("/")
        self.path, self.name = "/".join(x[:-1])+"/", x[-1]
        self.opts = kwargs
        self.proc = None
        if _winsound and self.name[-3:] != ".wav":
            raise RuntimeError("Winsound can not open this! Please ensure it is a wave file")
    def __str__(self):
        return "{1}\n{0}".format(
        self.path, self.name
        )
    if _winsound == False:
        def __enter__(self):
            self.proc = subprocess.Popen("{} -loglevel quiet -nodisp {} \"{}\"".format(
            _ffplay,
            " ".join((("-"+str(k)+" "+str(self.opts[k]) if self.opts[k] else "") for k in self.opts)),
            self.file))
            print("start")
        def __exit__(self, *args):
            print(args)
            if not self.proc.poll():
                print("terminate")
                self.proc.terminate()
        def wait(self):
            if not self.proc.poll():
                print("wait")
                self.proc.wait()
    else:
        def __enter__(self):
            pass
        def __exit__(self, *args):
            pass
        def wait(self):
            pass

class Volume:

    __volume = None

    def __init__(self, sync: int=0):
        if sync != False or self.__volume is None:
            self.sync(sync)

    def __constrain(self, val: int, min: int=0, max: int=100):
        return (min if val < min else (max if val > max else val))

    def __volume_up(self):
        sinput.key(keys.VOLUME_UP)

    def __volume_down(self):
        sinput.key(keys.VOLUME_DOWN)

    def set(self, vol: int=0, rel: bool=False):
        if rel:
            vol += self.__volume
        vol = self.__constrain(vol)
        diff = vol - self.__volume
        if diff > 0:
            for i in range(abs(diff // 2)):
                self.__volume_up()
        elif diff < 0:
            for i in range(abs(diff // 2)):
                self.__volume_down()
        self.__volume = vol // 2 * 2
        return self.volume()

    def up(self, amt: int=2):
        self.set(amt, True)
    def down(self, amt: int=2):
        return self.up(-amt)

    def volume(self):
        return self.__volume

    def sync(self, value: int=0):
        for i in range(50):
            self.__volume_down()
        self.__volume = self.__constrain(value) // 2 * 2
        for i in range(self.__volume // 2):
            self.__volume_up()

class media:

    @staticmethod
    def pause():
        sinput.key(keys.MEDIA_PLAY_PAUSE)
    play = pause

    @staticmethod
    def next():
        sinput.key(keys.MEDIA_NEXT_TRACK)

    @staticmethod
    def prev():
        sinput.key(keys.MEDIA_PREV_TRACK)
