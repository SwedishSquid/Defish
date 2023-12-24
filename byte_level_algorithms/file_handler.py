from byte_bit_buffer import ByteBitBuffer


def read_file_stream(file_path):
    with open(file_path, 'rb') as f:
        buffer = ByteBitBuffer()
        step = 10000
        while True:
            if not buffer.has_bytes():
                buffer.append_bytes_str(f.read(step))
            if not buffer.has_bytes():
                break
            yield buffer.pop_byte()
    pass


def read_file_segment_stream(file_path, start_pos: int, length: int):
    buffer = ByteBitBuffer()
    step = 10000
    with open(file_path, 'rb') as f:
        f.seek(start_pos)
        while True:
            if not buffer.has_bytes():
                read_count = min(step, length)
                buffer.append_bytes_str(f.read(read_count))
                length -= read_count
            if not buffer.has_bytes():
                break
            yield buffer.pop_byte()
    pass


def write_to_file_limited(file_path, sequence, limit_in_bytes, mode='wb'):
    """returns limit left"""
    with open(file_path, mode) as f:
        byte_buffer = ByteBitBuffer()
        step = 10000
        while limit_in_bytes > 0:
            for i, byte in enumerate(sequence):
                byte_buffer.append_byte(byte)
                if i >= step:
                    break
            if not byte_buffer.has_bytes():
                break
            limit_in_bytes -= len(byte_buffer.byte_buffer)
            f.write(b''.join(byte_buffer.pop_all_bytes()))
    return limit_in_bytes
