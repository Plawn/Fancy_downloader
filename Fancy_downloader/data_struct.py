from typing import List
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Chunk:
    start: int
    end: int
    last: int


@dataclass_json
@dataclass
class DownloadProgressSave:
    url: str
    filename: str
    size:int
    name: str
    type: str
    chunks: List[Chunk]
