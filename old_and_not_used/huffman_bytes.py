from core_algorithms.huffman_core import HuffmanDataBlock, HuffmanEncoderCore, HuffmanDecoderCore
import struct
import math
from itertools import chain


class CodeRecord:
    def __init__(self, value: bytes, code_len_bits: bytes, packed_code_list: list):
        if len(value) != 1:
            raise ValueError(f'value must be exactly 1 byte')
        self.value = value
        self.packed_code_len_bits = code_len_bits
        self.packed_code_list = packed_code_list
        pass

    def to_bytes_list(self):
        return [self.value, self.packed_code_len_bits] + self.packed_code_list
    pass


class SimpleHuffmanToBytes:
    """DEPRECATED
    takes blocks with items of type byte only"""
    """FORMAT of a block
    -Headers(+)
    --headers_length_bytes 2B
    --Code_table(+)
    ---table_length_bytes 2B
    ---Table(+)
    ----repeated:
    -----Code_record:
    ------byte_value 1B
    ------code_length_in_bits 1B
    ------code [ceil(code_length_in_bits/8)]B
    -Data(+)
    --data_length_bytes 4B
    --Encoded_data(+)
    ---repeated
    ----code ?bits
    --zero_filler_bits [?<8]bits
    """
    def __init__(self):
        self.buffer = []
        self.byte_buffer = 0
        self.byte_buffer_pos = 0
        pass

    def encode(self, iterator):
        for block in iterator:
            self.encode_block(block)
            for byte in self.buffer:
                yield byte
        pass

    def encode_block(self, block: HuffmanDataBlock):
        self.buffer.clear()
        self.byte_buffer = 0
        self.byte_buffer_pos = 0
        self.write_headers(block)
        self.write_data_section(block)
        pass

    def write_data_section(self, block: HuffmanDataBlock):
        zero_byte = struct.pack('<B', 0)
        len_section_pos = len(self.buffer)
        for _ in range(4):          # place for data section length
            self.buffer.append(zero_byte)

        data_section_length_bytes = 4

        for code in block.data:
            data_section_length_bytes += self.push_code_array_to_buffer(code)
        if self.byte_buffer_pos > 0:
            self.flush_byte_buffer()
            data_section_length_bytes += 1

        data_len_packed_list = [struct.pack('<B', b) for b in struct.pack('<I', data_section_length_bytes)]
        for i in range(4):
            self.buffer[len_section_pos + i] = data_len_packed_list[i]
        pass

    def write_headers(self, block: HuffmanDataBlock):
        headers_buffer = []
        code_table_len = 2
        for value, code in block.item_to_code:
            if type(value) != bytes or len(value) != 1:
                raise ValueError(f'value must be bytes of len 1. got {value}')
            code_record = self.make_code_record(value=value, code=code)
            code_record_bytes = code_record.to_bytes_list()
            code_table_len += len(code_record_bytes)
            for byte in code_record_bytes:
                headers_buffer.append(byte)
        headers_len = 2 + code_table_len
        headers_len_bytes = struct.pack('<H', headers_len)
        code_table_len_bytes = struct.pack('<H', code_table_len)
        for byte in [struct.pack('<B', b) for b in chain(headers_len_bytes, code_table_len_bytes)]:
            self.buffer.append(byte)
        for byte in headers_buffer:
            self.buffer.append(byte)
        pass

    def push_code_array_to_buffer(self, code: list):
        code_len_bits = len(code)
        bytes_pushed = 0
        for index in range(code_len_bits):
            bytes_pushed += self.push_bit_to_byte_buffer(code[index])
        return bytes_pushed

    def push_bit_to_byte_buffer(self, bit: bool):
        bytes_pushed = 0
        if self.byte_buffer_pos == 8:
            self.flush_byte_buffer()
            bytes_pushed += 1
        if bit:
            self.byte_buffer |= (1 << self.byte_buffer_pos)
        self.byte_buffer_pos += 1
        return bytes_pushed

    def flush_byte_buffer(self):
        byte = struct.pack('<B', self.byte_buffer)
        self.buffer.append(byte)
        self.byte_buffer = 0
        self.byte_buffer_pos = 0
        pass

    def make_code_record(self, value: bytes, code: list):
        packed_code_list, code_len_bits = self.code_to_bytes(code)
        packed_length = struct.pack('<B', code_len_bits)
        return CodeRecord(value=value, code_len_bits=packed_length, packed_code_list=packed_code_list)

    def code_to_bytes(self, code: list):
        code_len_bits = len(code)
        if code_len_bits <= 0:
            raise ValueError(f'code must contain elements')
        num = 0
        for i in range(code_len_bits):
            if code[i]:
                num |= (1 << i)
        code_len_in_bytes = math.ceil(code_len_bits / 8)
        pack_format = '<B'
        if code_len_in_bytes == 2:
            pack_format = '<H'
        elif code_len_in_bytes > 2:
            pack_format = '<I'
        packed_code = struct.pack(pack_format, num)
        packed_code_list = [struct.pack('<B', b) for b in packed_code]
        return packed_code_list, code_len_bits
    pass




text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'

data = text * 10

bytes_list_data = [char.encode() for char in data]



print('row data bytes list ----------')
print(bytes_list_data)

result_core = list(HuffmanEncoderCore(10000).encode(iter(bytes_list_data)))

# translation = [(block.item_to_code, block.data) for block in result_core]


result_byte = list(SimpleHuffmanToBytes().encode(iter(result_core)))
print('encoded bytes list ---------------')
print(result_byte)
print(b''.join(result_byte))

print(f'symbol length = {len(data)}')
print(f'byte length = {len(result_byte)}')
print(b''.join(result_byte))


decoded = list(HuffmanDecoderCore().decode(iter(result_core), lambda x: id(x)))



print(len(result_core))
print(data)
# print(translation)
print(b''.join(decoded))
print(result_core[0].item_to_code)

