"""I/O meter with totals across streams and the largest operation per stream.

Correct solution for io_meter after c_totals.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from meter import IOMeter
    meter = IOMeter()
    meter.open_stream("log")
    meter.record_read("log", 4096)
    meter.get_total_bytes()
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
        self.largest = 0

    @property
    def ops(self):
        return self.reads + self.writes


class IOMeter:
    def __init__(self):
        self._streams = {}  # stream id -> _Stream, in opening order

    def open_stream(self, stream_id):
        if not isinstance(stream_id, str) or not stream_id:
            raise ValueError("stream_id must be a non-empty str")
        if stream_id in self._streams:
            raise MeterError(f"stream {stream_id!r} is already open")
        self._streams[stream_id] = _Stream()

    def record_read(self, stream_id, size):
        stream = self._require(stream_id)
        check_size(size)
        stream.bytes_read += size
        stream.reads += 1
        stream.largest = max(stream.largest, size)

    def record_write(self, stream_id, size):
        stream = self._require(stream_id)
        check_size(size)
        stream.bytes_written += size
        stream.writes += 1
        stream.largest = max(stream.largest, size)

    def get_bytes_read(self, stream_id):
        return self._require(stream_id).bytes_read

    def get_bytes_written(self, stream_id):
        return self._require(stream_id).bytes_written

    def get_op_counts(self, stream_id):
        stream = self._require(stream_id)
        return (stream.reads, stream.writes)

    def get_streams(self):
        return list(self._streams)

    def get_total_bytes(self):
        streams = self._streams.values()
        return (sum(s.bytes_read for s in streams), sum(s.bytes_written for s in streams))

    def get_total_ops(self):
        return sum(s.ops for s in self._streams.values())

    def get_largest_op(self, stream_id):
        return self._require(stream_id).largest

    def get_busiest_stream(self):
        if not self._streams:
            raise MeterError("no stream is open")
        # max() keeps the first of equally busy streams, i.e. the one opened first.
        return max(self._streams, key=lambda s: self._streams[s].ops)

    def _require(self, stream_id):
        # Non-str ids are never stored, so they count as "not open" too.
        if not isinstance(stream_id, str) or stream_id not in self._streams:
            raise KeyError(stream_id)
        return self._streams[stream_id]
