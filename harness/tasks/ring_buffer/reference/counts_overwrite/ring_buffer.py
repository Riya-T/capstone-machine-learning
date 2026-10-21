"""Ring buffer with an overwrite mode and lifetime totals.

Correct solution for ring_buffer after c_overwrite and c_counts.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ring_buffer import RingBuffer
    buf = RingBuffer(3)
    buf.enable_overwrite()
    buf.write(10)
    buf.get_total_written()  # 1
"""


class RingError(Exception):
    pass


class BufferFull(RingError):
    pass


class BufferEmpty(RingError):
    pass


def check_value(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"value must be an int, got {value!r}")


class RingBuffer:
    def __init__(self, capacity):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError(f"capacity must be an int >= 1, got {capacity!r}")
        self._slots = [None] * capacity  # fixed storage, used as a ring
        self._head = 0  # slot of the oldest value
        self._count = 0  # values currently held
        self._overwrite = False
        self._written = 0
        self._read = 0
        self._discarded = 0

    def write(self, value):
        check_value(value)
        if self._count == len(self._slots):
            if not self._overwrite:
                raise BufferFull("buffer is full")
            # Replace the oldest value; the one after it becomes the oldest.
            self._slots[self._head] = value
            self._head = self._slot(1)
            self._discarded += 1
        else:
            self._slots[self._slot(self._count)] = value
            self._count += 1
        self._written += 1

    def read(self):
        self._require_values()
        value = self._slots[self._head]
        self._slots[self._head] = None
        self._head = self._slot(1)
        self._count -= 1
        self._read += 1
        return value

    def clear(self):
        self._discarded += self._count
        self._slots = [None] * len(self._slots)
        self._head = 0
        self._count = 0

    def get_size(self):
        return self._count

    def get_capacity(self):
        return len(self._slots)

    def enable_overwrite(self):
        self._overwrite = True

    def disable_overwrite(self):
        self._overwrite = False

    def is_overwrite_enabled(self):
        return self._overwrite

    def get_total_written(self):
        return self._written

    def get_total_read(self):
        return self._read

    def get_total_discarded(self):
        return self._discarded

    def _slot(self, offset):
        # The slot `offset` places after the oldest value, wrapping around.
        return (self._head + offset) % len(self._slots)

    def _require_values(self):
        if self._count == 0:
            raise BufferEmpty("buffer is empty")
