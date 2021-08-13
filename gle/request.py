import io
import enum
import asyio
import pytube
import asyncio
import functools
import urllib.parse
import urllib.request
from typing import Union
from bs4 import BeautifulSoup
from interface import Interface
from dataclasses import dataclass
from youtube_search import YoutubeSearch as _YoutubeSearch

USER_AGENT = {"User-Agent": r"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}

class Request:

    _request_done = False

    def __init__(self):
        pass

    def __await__(self):
        return self._call().__await__()

    async def _call(self):
        await self._request()
        self._request_done = True
        return self

    async def _request(self):
        pass

    def _require(func):
        """Wrapper that will raise if request has not been made yet"""
        @functools.wraps(func)
        def require_request(self, *args, **kwargs):
            if not self._request_done:
                raise ValueError
            return func(self, *args, **kwargs)
        return require_request

    def _ensure(func):
        """Wrapper that make the request if it has not already done so"""
        @functools.wraps(func)
        async def ensure_request(self, *args, **kwargs):
            if not self._request_done:
                await self.request()
                self._request_done = True
            return await func(self, *args, **kwargs)
        return ensure_request

    def _clear(self):
        """Clears the request cache"""
        self._request_done = False

class Search(Request):

    SITE = r"https://www.google.com/search?"
    @dataclass
    class Result:
        url: str
        title: str

    def __init__(self, *terms: str, count: int=10, site: str=None):
        self.terms = terms
        self.count = count
        self.site = site

        self._req_results = []

    async def _request(self):
        params = {"q":self.terms, "num":str(max(1, int(self.count)))}
        if self.site is not None:
            params["as_sitesearch"] = self.site
        response = await asyio.Request(urllib.request.Request(self.SITE +
        urllib.parse.urlencode(params),
        headers=USER_AGENT))

        soup = BeautifulSoup(response.read(), "html.parser")
        # Parse Results
        self._req_results.clear()
        for row in soup("div", "g"):
            title = row.find("span").string
            if title:
                url = row.find("a", href=True)["href"]
                if not url.startswith("/"):
                    self._req_results.append(self.Result(url, title))

    @property
    @Request._require
    def results(self):
        return self._req_results

async def search(*args, **kwargs):
    req = Search(*args, **kwargs)

class Lyrics(Request):

    SITE = r"https://www.google.com/search?"

    def __init__(self, title: str, artist: str=None):
        self.rtitle, self.rartist = title, artist
        self._req_title, self._req_artist = "", ""
        self._req_lyrics = []

    async def _request(self):
        response = await asyio.Request(urllib.request.Request(self.SITE +
        urllib.parse.urlencode({"q": f"{self.rtitle} {self.rartist+' ' if self.rartist is not None else ''}lyrics"}),
        headers=USER_AGENT))

        soup = BeautifulSoup(response.read(), "html.parser")
        # Retrive Name and Artist
        subtitle: Tag = soup.find("div", {"data-attrid":"subtitle"})
        title_name = subtitle.previousSibling.find("span").string
        artist_name = subtitle.find("a").string

        # Retrive Lyrics
        lyrics: Tag = soup.find("div", {"data-lyricid":True})
        block_children = lyrics.children
        lines = []
        for child in [next(block_children) for i in range(2)]:
            for c in list(child.children)[:-1]:
                for s in c.find_all("span"):
                    lines.append(s.string)
                lines.append("")
        lines.pop()
        self._req_title, self._req_artist = title_name, artist_name
        self._req_lyrics = lines

    @property
    @Request._require
    def lyrics(self):
        return self._req_lyrics
    @property
    @Request._require
    def title(self):
        return self._req_title
    @property
    @Request._require
    def artist(self):
        return self._req_artist

class Youtube(Request):

    SITE = r"https://www.youtube.com/results?"
    URL = r"https://www.youtube.com/watch?v={}"
    @dataclass
    class Video:
        id: str
        title: str
        channel: str
        duration: int

    def __init__(self, *terms):
        self.terms = terms
        self._req_videos = []

    async def _request(self):
        response: _YoutubeSearch = await Interface.process(_YoutubeSearch, " ".join(self.terms))
        for vid in response.videos:
            time = vid["duration"].split(":")
            h,m,s = [0] * (3-len(time)) + time
            self._req_videos.append(self.Video(vid["id"], vid["title"], vid["channel"], int(h)*3600+int(m)*60+int(s)))

    @property
    @Request._require
    def videos(self) -> list[Video]:
        return self._req_videos

class YoutubeDownload(Request):

    class Stream(enum.IntEnum):
        Audio = 1
        Video = 2
        AuVid = 3

    def __init__(self, url: Union[str, Youtube.Video], stream: Stream=Stream.Audio):
        self.url = "v="+url.id if isinstance(url, Youtube.Video) else url
        self.stype = stream
        self._req_mem = io.BytesIO()

    async def _request(self):
        try:
            response: pytube.YouTube = await Interface.process(pytube.YouTube, self.url)
        except Exception as exc:
            raise
        mem = io.BytesIO()
        if self.stype is self.Stream.Audio:
            stream = await Interface.process(lambda: response.streams.filter(only_audio=True).order_by("abr").last())
        else:
            raise ValueError("IM LAZY FIX ME")
        await Interface.process(stream.stream_to_buffer, mem)
        mem.seek(0, 0)
        self._req_mem = mem

    @property
    @Request._require
    def memory(self):
        return self._req_mem
