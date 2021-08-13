from .base import Properties, Processor
from .ffmpeg import FFmpegProcessor
import numpy as np

__all__ = ["Cast", "Speed", "Volume"]

class Cast(FFmpegProcessor):
    def __init__(self):
        super().__init__("-i {pipe} -vn -f {prop.fmt} -ac {prop.channels} -ar {prop.samplerate} {pipe}")

class Speed(FFmpegProcessor):
    def __init__(self, value: float=1.0):
        super().__init__("-f {prop.fmt} -ac {prop.channels} -ar {irate} -i {pipe} -vn -f {prop.fmt} -ac {prop.channels} -ar {prop.samplerate} {pipe}")
        self._value = value
    def open(self, properties: Properties) -> bool:
        return super().open(properties, irate=int(properties.samplerate * self._value))

class Echo(FFmpegProcessor):
    def __init__(self, igain: float=0.6, ogain: float=0.3, delays: float=1000, decays: float=0.5):
        super().__init__("""-f {prop.fmt} -ac {prop.channels} -ar {prop.samplerate} -i {pipe} -vn -y -f {prop.fmt} -ac {prop.channels} -ar {prop.samplerate} -af "aecho={igain}:{ogain}:{delays}:{decays}" {pipe}""")
        self.igain, self.ogain, self.delays, self.decays = igain, ogain, delays, decays
    def open(self, properties: Properties) -> bool:
        return super().open(properties,
            igain=self.igain, ogain=self.ogain,
            delays=(self.delays if isinstance(self.delays, (int, float)) else "|".join(map(str, self.delays))),
            decays=(self.decays if isinstance(self.decays, (int, float)) else "|".join(map(str, self.decays))),
        )

class Volume(Processor):
    def __init__(self, value: float=1.0):
        super().__init__()
        self.value: float = value
        # 1.0 == 100%
    async def process(self, data: np.ndarray, size: int) -> np.ndarray:
        return data * self.value
