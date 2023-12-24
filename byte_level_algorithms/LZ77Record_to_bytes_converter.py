from core_algorithms.LZ77_core import LZ77Record
from byte_bit_buffer import ByteBitBuffer
import struct


class LZ77RecordToBytesConverter:
    """window width < 256
    item == byte
    length < 256"""
    def encode(self, record_stream):
        buffer = ByteBitBuffer()
        for r in record_stream:
            r: LZ77Record = r
            buffer.append_bytes_str(struct.pack('<B', r.lookback_index))
            if r.lookback_index != 0:
                buffer.append_bytes_str(struct.pack('<B', r.length))
            else:
                buffer.append_byte(r.item)
            while buffer.has_bytes():
                yield buffer.pop_byte()
        pass

    def decode(self, byte_stream):
        buffer = ByteBitBuffer()
        while True:
            try:
                buffer.append_byte(next(byte_stream))
                lookback_index = \
                struct.unpack('<B', b''.join(buffer.pop_n_bytes(1)))[0]
                if lookback_index != 0:
                    buffer.append_byte(next(byte_stream))
                    length = \
                    struct.unpack('<B', b''.join(buffer.pop_n_bytes(1)))[
                        0]
                    yield LZ77Record(lookback_index, length)
                else:
                    item = next(byte_stream)
                    yield LZ77Record(lookback_index, 1, item)
            except StopIteration:
                break
        pass
    pass
