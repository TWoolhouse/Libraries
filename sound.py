import sinput
import subprocess
import time
import winsound

# cmd = "ffplay -loglevel quiet -nodisp \""+file+"\""
# os.system(cmd)
# song = subprocess.Popen(cmd)
# song.terminate()

_ffplay = "D:/Programs/ffmpeg/bin/ffplay.exe"
_winsound = True
_volume = None

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

    def __init__(self, vol=0):
        global _volume
        if _volume == None:
            for i in range(50):
                self._volume_down()
            _volume = self.constrain(vol) // 2 * 2
            for i in range(_volume // 2):
                self._volume_up()

    def constrain(self, val, min=0, max=100):
        return (min if val < min else (max if val > max else val))

    def _volume_up(self):
        sinput.key(sinput.VK.VOLUME_UP)

    def _volume_down(self):
        sinput.key(sinput.VK.VOLUME_DOWN)

    def set_volume(self, vol=0, rel=False):
        global _volume
        if rel:
            vol += _volume
        vol = self.constrain(vol)
        diff = vol - _volume
        if diff > 0:
            for i in range(abs(diff // 2)):
                self._volume_up()
        elif diff < 0:
            for i in range(abs(diff // 2)):
                self._volume_down()
        _volume = vol // 2 * 2
        return self.volume()

    def volume(self):
        global _volume
        return _volume

class Media:

    def pause(self):
        sinput.key(sinput.VK.MEDIA_PLAY_PAUSE)
    play = pause

    def next(self):
        sinput.key(sinput.VK.MEDIA_NEXT_TRACK)

    def prev(self):
        sinput.key(sinput.VK.MEDIA_PREV_TRACK)
