import sinput
import subprocess
import time

file = "C:/Users/Tom/Music/Persona 5/1-03. Escape.mp3"
cmd = "ffplay -loglevel quiet -nodisp \""+file+"\""
#os.system(cmd)
#song = subprocess.Popen(cmd)
#song.terminate()

class Song:
    def __init__(self, file):
        self.file = file.replace("\\", "/")
        x = self.file.split("/")
        self.path, self.name = "/".join(x[:-1])+"/", x[-1]
    def __str__(self):
        return "{1}\n{0}".format(
        self.path, self.name
        )
    def __enter__(self):
        pass
    def __exit__(self):
        pass

print(Song(file))

def volume_up():
    sinput.key(sinput.VK.VOLUME_UP)

def volume_down():
    sinput.key(sinput.VK.VOLUME_DOWN)

def set_volume(int):
    for _ in range(0, 50):
        volume_down()
    for _ in range(int // 2):
        volume_up()

#sinput.move(50, 0, True)
#sinput.click(1)
#set_volume(40)
