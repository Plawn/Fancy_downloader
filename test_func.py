from dataclasses import dataclass
from typing import List


@dataclass
class Split:
    start: int
    end: int

    def as_range(self):
        return f'{self.start}-{self.end}'


size = 7760957


def split(size: int, chunks_nb: int, offset: int = 0) -> List[Split]:
    if chunks_nb == 1:
        return [Split(0, size)]
    chunk_size = (size - offset) // chunks_nb
    l = [(
        0,
        chunk_size
    )]
    l.extend(
        (1 + i * chunk_size, (i + 1) * chunk_size)
        for i in range(1, chunks_nb - 1)
    )
    l.append((
        (chunks_nb - 1) * chunk_size,
        (size - offset)
    ))
    return [
        Split(start + offset, end + offset) for start, end in l
    ]

first_splits = split(size, 5, 6507964)
# first_split = first_splits[0]
print(first_splits)

# second_level_split = split(first_split.end - first_split.start, 2, first_split.start)
# print(second_level_split)