"""I/O meter: bytes read and written, and operation counts, per named stream.

Planted bug (initial version): open_stream on an id that is already open
silently resets the stream instead of raising MeterError. The public checks
never reopen a stream, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from meter import IOMeter
    meter = IOMeter()
    meter.open_stream("log")
    meter.record_read("log", 4096)
"""


class MeterError(Exception):
    pass


def check_size(size):
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ValueError(f"size must be an int >= 0, got {size!r}")


class _Stream:
    def __init__(self):
        self.bytes_read = 0
        self.bytes_written = 0
        self.reads = 0
        self.writes = 0


class IOMeter:
    def __init__(self):
        self._streams = {}  # stream id -> _Stream, in opening order

    def open_stream(self, stream_id):
        if not isinstance(stream_id, str) or not stream_id:
            raise ValueError("stream_id must be a non-empty str")
        self._streams[stream_id] = _Stream()

    def record_read(self, stream_id, size):
        stream = self._require(stream_id)
        check_size(size)
        stream.bytes_read += size
        stream.reads += 1

    def record_write(self, stream_id, size):
        stream = self._require(stream_id)
        check_size(size)
        stream.bytes_written += size
        stream.writes += 1

    def get_bytes_read(self, stream_id):
        return self._require(stream_id).bytes_read

    def get_bytes_written(self, stream_id):
        return self._require(stream_id).bytes_written

    def get_op_counts(self, stream_id):
        stream = self._require(stream_id)
        return (stream.reads, stream.writes)

    def get_streams(self):
        return list(self._streams)

    def _require(self, stream_id):
        # Non-str ids are never stored, so they count as "not open" too.
        if not isinstance(stream_id, str) or stream_id not in self._streams:
            raise KeyError(stream_id)
        return self._streams[stream_id]
