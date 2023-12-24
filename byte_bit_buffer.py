from collections import deque
import struct


class ByteBitBuffer:
    def __init__(self):
        self.byte_buffer = deque()
        self.input_bit_buffer = []
        self.output_bit_buffer = deque()
        pass

    def append_byte(self, byte: bytes):
        if not self.can_append_byte():
            raise ValueError(f'cant append bytes - bits buffer not empty')
        if len(byte) != 1:
            raise ValueError(f'expected bytes of len 1; got "{byte}" of len {len(byte)}')
        self.byte_buffer.append(byte)
        pass

    def append_bytes_str(self, bytes_str: bytes):
        for i in range(len(bytes_str)):
            self.append_byte(bytes_str[i:i+1])
        pass

    def can_append_byte(self):
        return len(self.input_bit_buffer) == 0

    def append_byte_sequence(self, sequence):
        if type(sequence) == bytes:
            self.append_bytes_str(sequence)
            return
        for byte in sequence:
            self.append_byte(byte)
        pass

    def append_bit(self, bit: bool):
        self.input_bit_buffer.append(bit)
        if len(self.input_bit_buffer) == 8:
            self.flush_bit_buffer()
        pass

    def flush_bit_buffer(self):
        """return amount of significant flushed bits"""
        significant_bit_count = len(self.input_bit_buffer)
        if len(self.input_bit_buffer) == 0:
            return significant_bit_count
        byte_will_be = 0
        bit_position = 0

        for bit in self.input_bit_buffer:
            if bit:
                byte_will_be |= 1 << bit_position
            bit_position += 1
        byte = struct.pack('<B', byte_will_be)
        self.input_bit_buffer.clear()
        self.append_byte(byte)
        return significant_bit_count

    def has_bytes(self):
        return (len(self.byte_buffer) > 0) or (len(self.input_bit_buffer) > 0)

    def has_bits(self, threshold=0):
        """0 <= amount <= 7"""
        return self.has_bytes() or (len(self.output_bit_buffer) > threshold)

    def pop_byte(self):
        if not self.has_bytes():
            raise IndexError('no elements to pop')
        if len(self.byte_buffer) == 0 and len(self.input_bit_buffer) > 0:
            self.flush_bit_buffer()
        return self.byte_buffer.popleft()

    def pop_n_bytes(self, n):
        result = []
        for i in range(n):
            result.append(self.pop_byte())
        return result

    def pop_all_bytes(self):
        result = []
        while self.has_bytes():
            result.append(self.pop_byte())
        return result

    def fill_bit_buffer(self):
        if len(self.output_bit_buffer) > 0:
            return
        was_byte = struct.unpack('<B', self.pop_byte())[0]
        for i in range(8):
            if was_byte & (1 << i) != 0:
                self.output_bit_buffer.append(True)
            else:
                self.output_bit_buffer.append(False)
        pass

    def pop_bit(self):
        if len(self.output_bit_buffer) == 0:
            self.fill_bit_buffer()
        return self.output_bit_buffer.popleft()

    def discard_bits_in_output_bit_buffer(self):
        self.output_bit_buffer.clear()
        pass

    def get_full_bytes_len(self):
        return len(self.byte_buffer)
    pass


def test():
    buffer = ByteBitBuffer()

    sequence = [True, False, False, False, True, True, False, True, True, True]

    for bit in sequence:
        buffer.append_bit(bit)

    while buffer.has_bits():
        bit = buffer.pop_bit()
        print(bit)


def test2():
    buffer = ByteBitBuffer()
    stri = 'helloworld'.encode()
    print(stri)
    buffer.append_bytes_str(stri)
    while buffer.has_bytes():
        print(buffer.pop_byte())
