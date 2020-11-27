import sinput
import keys

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

class Media:

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
