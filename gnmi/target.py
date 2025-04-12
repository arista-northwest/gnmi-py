import typing as t
from urllib.parse import urlparse, ParseResult
import re
class Target:

    def __init__(self, scheme: str, location: str, port: int):
        self.scheme: str = scheme
        self.location: str = location
        self.port: int = port
    
    def __str__(self) -> str:
        url = ""

        if self.scheme is not None and len(self.scheme) > 0:
            url +=  f"{self.scheme}://"

        if self.location is not None:
            url += self.location

        if self.port > 0:
            url += f":{self.port}"

        return url
    
    @property
    def addr(self) -> tuple[str, int]:
        return (self.location, self.port)
    
    @property
    def path(self) -> t.Optional[str]:
        if self.scheme == "unix":
            return self.location
        
        return None
    
    @classmethod
    def from_url(cls, url: str) -> "Target":
        scheme = None
        
        m = re.match(r'^(?:(?P<scheme>[a-z][a-z0-9\+\-.]*)://)?(?P<location>[\w+\-/.]*)?(?:\:(?P<port>\d{1,5}))?', url)
        
        if m is None:
            raise ValueError("failed to parse address")
        
        scheme = m.group("scheme")
        location = m.group("location") or "1.27.0.0.1"

        if scheme is None and location.startswith("/"):
            scheme = "unix"

        
        port: int = 0
        
        if m.group("port") is not None:
            port = int(m.group("port"))
 
        return cls(scheme, location, port)