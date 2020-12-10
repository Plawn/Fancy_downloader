from dataclasses import dataclass


@dataclass
class Split:
    start: int
    end: int

    def as_range(self):
        return f'{self.start}-{self.end}'


size = 100000456


chunks_nb = 2

print(size // chunks_nb)


def split(size: int, chunks_nb: int) -> list:
    if chunks_nb == 1:
        return [Split(0, size)]
    chunk_size = size // chunks_nb
    l = [Split(0, chunk_size)]
    l.extend(Split(i * chunk_size + 1, (i+1)*chunk_size)
             for i in range(1, chunks_nb - 1))
    l.append(Split((chunks_nb - 1) * chunk_size, size))
    return l


l = (split(size, chunks_nb))
print(len(l))
print(l)
