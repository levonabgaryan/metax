from typing import Iterator


def get_batch_from_iterator[T](iterator: Iterator[T], batch_size_: int) -> list[T]:
    # This function must be used in a thread, when iterator or generator include IO task
    batch_ = []
    for _ in range(batch_size_):
        try:
            item = next(iterator)
            batch_.append(item)
        except StopIteration:
            break
    return batch_
